"""Get the FFmpeg file formats."""
import subprocess
import sys


class FFmpegFileFormats:
    """Get the FFmpeg file formats."""
    @staticmethod
    def get_ffmpeg_formats() -> list:
        """Get the FFmpeg file formats.

        Returns:
            list: The FFmpeg file formats.
        """
        def parse_ffmpeg_formats(output) -> list:
            """Parse the FFmpeg formats output.

            Args:
                output (str): The FFmpeg formats output.

            Returns:
                list: The FFmpeg file formats.
            """
            formats = []
            lines = output.splitlines()
            parsing_formats = False

            for line in lines:
                if line.strip().startswith('--'):
                    parsing_formats = True
                    continue

                if parsing_formats and line.strip() == '':
                    break

                if parsing_formats:
                    if line.strip().startswith(('D', 'E', 'DE')):
                        parts = line.strip().split(None, 2)
                        if len(parts) >= 2: # noqa
                            direction = parts[0]
                            format_name = parts[1]
                            description = parts[2] if len(parts) > 2 else '' # noqa
                            formats.append({
                                'direction': direction,
                                'format_name': format_name,
                                'description': description
                            })
            return formats

        try:
            result = subprocess.run(
                ['ffmpeg', '-formats', '-hide_banner'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                check=False
            )
            output = result.stdout
            formats = parse_ffmpeg_formats(output)

            format_extensions = [f['format_name'] for f in formats]
            # Add '.' prefix to the format extensions
            return ['.' + ext for ext in format_extensions]

        except FileNotFoundError:
            print('FFmpeg is not installed or not found in the system PATH.')
            print('Exiting...')
            sys.exit(1)
        except Exception as e:
            print(f'An error occurred: {e}')
            print('Exiting...')
            sys.exit(1)
