"""Generates a report based on a template and data from a JSON file."""
from datetime import datetime
from datetime import timezone
from pathlib import Path

import jinja2
import jmespath
import orjson
import yaml
from docxtpl import DocxTemplate
from openpyxl import load_workbook


RES_DIR = Path('res')


class GenerateLog:
    """Generates a report based on a template and data from a JSON file."""

    def __init__(self, workdir: Path, base_url: str, ds_metadata: dict) -> None:
        """Initializes the GenerateLog class.

        Args:
            workdir (Path): The working directory.
            base_url (str): The base URL of the repository.
            ds_metadata (dict): The dataset metadata.
        """
        self.workdir = workdir
        # self.config = self._read_config_yaml()
        self.timestamp = self._get_timestamp()
        self.ds_metadata = ds_metadata
        self.base_url = base_url
        self.dataset_info_dict = self._get_dataset_info()

    @staticmethod
    def _get_timestamp() -> str:
        """Returns the current timestamp and return it as a dictionary.

        Returns:
            str : The current timestamp in 'YYYY-MM-DD HH:MM:SS' format.
        """
        utc_now = datetime.now(tz=timezone.utc)
        local_now = utc_now.astimezone()
        return local_now.strftime('%Y-%m-%d %H:%M:%S')

    def _get_dataset_info(self) -> dict:
        """Returns the dataset information as a dictionary.

        Returns:
            dict: The dataset information.
        """
        search_string = """{
        DatasetTitle: join(', ', data.latestVersion.metadataBlocks.citation.fields[?typeName==`title`].value),
        DatasetPersistentId: data.latestVersion.datasetPersistentId,
        ID: data.latestVersion.id}"""
        dataset_info_dict = jmespath.search(search_string, self.ds_metadata)
        # Add 'DatasetURL' by parsing the base_url and the DatasetPersistentId
        dataset_info_dict['DatasetURL'] = f'{self.base_url}/dataset.xhtml?persistentId={dataset_info_dict.get('DatasetPersistentId', None)}'  # noqa: E501

        return dataset_info_dict

    @staticmethod
    def _get_config_info() -> dict:
        """Reads the config.yaml file and returns it as a dictionary.

        Returns:
            dict: The config as a dictionary.
        """
        with RES_DIR.joinpath('config.yaml').open(encoding='utf-8') as file:
            return yaml.safe_load(file)

    @staticmethod
    def read_template_json() -> dict:
        """Reads the template.json file and returns it as a dictionary.

        Returns:
            dict: The template as a dictionary.
        """
        with RES_DIR.joinpath('template.json').open(encoding='utf-8') as file:
            return orjson.loads(file.read())

    def generate_report_xlsx(self, template_dict: dict) -> None:
        """Fill a formatted Excel template with data using Jinja2 for variable replacement.

        Args:
            template_dict (dict): Dictionary of data to inject into the template
        """
        # Load the workbook with formatting
        template_path = Path(RES_DIR, 'template_new.xlsx')
        workbook = load_workbook(template_path)
        sheet = workbook.active

        # Create Jinja2 environment
        env = jinja2.Environment()

        # Process each cell in the worksheet to replace Jinja2 variables
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str) and '{%' in cell.value:
                    # This cell contains a Jinja2 template
                    template = env.from_string(cell.value)
                    try:
                        # Render the template with our data
                        cell.value = template.render(template_dict=template_dict)
                    except Exception as e:
                        print(f'Error rendering template in cell {cell.coordinate}: {e}')

        # Save the modified workbook
        excel_path_obj = self.workdir.joinpath('log_files', 'render_log_new.xlsx')
        workbook.save(excel_path_obj)
        print(f'\nExcel Spreadsheet curation log saved at: {str(excel_path_obj)}')

    def generate_report_doc(self, template_dict: dict) -> None:
        """Generates a report based on the provided template dictionary.

        Args:
            template_dict (dict): The template dictionary.
        """
        # Load the template
        template_path = Path(RES_DIR, 'template_new.docx')
        doc = DocxTemplate(template_path)

        # Render the document with the provided context
        doc.render({'template_dict': template_dict,  # TEMP fix. Need to restructure the template_dict
                    'timestamp': self.timestamp,
                    'dataset': self.dataset_info_dict,
                    'curator_info': self._get_config_info()})

        # Save the rendered document
        doc_path = self.workdir.joinpath('log_files', 'render_log.docx')
        doc.save(doc_path)
        print(f'\nWord curation log saved at: {str(doc_path)}')
