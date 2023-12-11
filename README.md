# ffder

----

## **Introducing ffder: a highly extensible, oneshop-for-all file loader**

----

ffder is a Python package designed to load and parse file contents into Python dictionaries. It supports various file formats, as it dynamically selects the appropriate loader for a given file format.

## Features

- lazy-import, install dependency as you needed it
- File discovery based on file names.
- Support for loading files in .env, .toml, .yaml/.yml, and .json formats.
- Chain of file loader classes that can be extended for additional formats.
- Caching strategy for loaded files to improve performance.
- Human-friendly error messages, exception handling for unsupported file formats.

## Requirements


To use specific file loaders, the ffder package requires the following:
> Install as you go, you don't have to install unused dependency.

- `python-dotenv` for `.env` files.
- `tomllib` (built-in for Python 3.11 and higher) or `toml` for older Python versions for `.toml` files.
- `PyYAML` for `.yaml` or `.yml` files.
- Standard `json` library for `.json` files.

Make sure to install the necessary dependencies for the file types you plan to work with.

## Usage

Before you can use the ffder package, install it and its dependencies according to your file format needs.

### Basic File Loading

Instantiate a `FileUtil` object and use it to read files. The `read_file` method tries to read the file with the supported format loaders. Here's a basic example of reading a `.json` file:

```python
from file_util import FileUtil

# Create a FileUtil instance
file_util = FileUtil()

# Read the contents of 'config.json' and return them as a dictionary
config_data = file_util.read_file('config.json')
```

### Handling Different File Formats

The package contains different loaders for `.env`, `.toml`, `.yaml`/`.yml`, and `.json` files. Based on the file extension, the appropriate loader is selected. For instance, reading a `.toml` file is done as follows:

```python
config_data = file_util.read_file('settings.toml')
```

### Registering New File Loaders
If you need to support a new file format, extend the `FileLoader` class and register the new loader:

```python
from file_util import FileLoader

class XMLFileLoader(FileLoader):
    supported_formats = ".xml"

    def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
        # Implement loading logic for

XML files here.
        import xml.etree.ElementTree as ET

        tree = ET.parse(file)
        root = tree.getroot()
        # Convert XML tree to a dictionary
        return self._xml_to_dict(root)

    def _xml_to_dict(self, root):
        # Recursive function to convert XML to a dictionary
        data = {root.tag: {} if root.attrib else None}
        children = list(root)
        if children:
            dd = defaultdict(list)
            for dc in map(self._xml_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            data = {root.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
        if root.text:
            text = root.text.strip()
            if children or root.attrib:
                if text:
                    data[root.tag]['text'] = text
            else:
                data[root.tag] = text
        return data

# Register the new XML loader
FileLoader.register(XMLFileLoader)
```

After registering the new loader, it becomes part of the chain and can be used automatically when reading files with the `.xml` extension:

```python
config_data = file_util
read_file('configuration.xml')
```

## Advanced Usage

### Customizing the File Loader Chain

By default, the `FileLoader.from_chain()` method constructs a chain of loaders in the reverse order of their declaration. To customize the order or to include custom loaders in the chain, manually create instances and set the `next` property.

```python
from file_util import FileUtil, JsonFileLoader, YAMLFileLoader, ENVFileLoader, TOMLFileLoader

# Manually create a custom chain of loaders
json_loader = JsonFileLoader()
yaml_loader = YAMLFileLoader()
env_loader = ENVFileLoader()
toml_loader = TOMLFileLoader()

# Set the order of loaders manually
json_loader.next = yaml_loader
yaml_loader.next = env_loader
env_loader.next = toml_loader

# Use the custom chain in FileUtil
file_util = FileUtil(file_loader=json_loader)

# Now the custom chain is used to load files
```

### Error Handling

The package raises specific exceptions for error scenarios, which can be handled by the consuming application:

```python
from file_util import FileUtil, UnsupportedFileFormatError, FileNotFoundError

file_util = FileUtil()

try:
    data = file_util.read_file('unknown_file.cfg')

except FileNotFoundError as e:
    print(f"Could not find the file: {e}")
except UnsupportedFileFormatError as e:
    print(f"The file format is not supported: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

This will ensure that your application can provide informative messages to the user or take appropriate action when an error is encountered.

### Caching File Reads

The `FileUtil` class uses caching for the `from_cwd()` class method allowing the reuse of a single `FileUtil` instance based on the current working directory, optimizing performance for repeated file reads in the same directory.

```python
# Retrieve the cached FileUtil instance based on the current working directory
file_util = FileUtil.from_cwd()

# Use this instance to read files as before
config_data = file_util.read_file('config.json')
```

## Conclusion

The ffder package offers a neat and extendable way to load and parse files in various formats into Python dictionaries. By following the examples in this README, you should be able to integrate it into your Python projects and easily handle configuration and data files.

Remember to include your new file loaders in the chain if you create them, and to handle exceptions gracefully for
a seamless user experience. With this package, managing file operations in Python becomes more structured and efficient.

## Contributing

Contributions to the ffder package are welcome. If you have a suggestion for a new feature, a bug report, or a new file loader implementation, please open an issue or submit a pull request on the package's repository.

When contributing, please ensure that:

- New code contributions adhere to the existing coding style and design patterns.
- New loaders extend the `FileLoader` base class and properly implement the `loads` method.
- Contributions are accompanied by appropriate tests to validate functionality.

We value your contributions in making ffder a robust and versatile package for the Python community.

For more information on how to contribute, please refer to the repository's CONTRIBUTING.md file.

## License

The ffder package is released under the [MIT License](https://opensource.org/licenses/MIT). Please see the LICENSE file in the repository for full details.

## Contact

If you have any questions, comments, or need further assistance regarding the ffder package, feel free to reach out to the maintainer(s) through the repository's issues section or the provided contact information.

----

Thank you for using or considering the ffder package for your file handling needs in Python.
