# By Filip Stehlik 11/26/2023
# CBUNS header file and xml validation script
# Made for KassowRobots in interview proccess

import re
import xml.etree.ElementTree as ET
import sys
import logging
from argparse import ArgumentParser

# setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class Validator:
    def __init__(self, header_file, xml_file):
        self.header_file = header_file
        self.xml_file = xml_file
        self.mandatory_methods = [
            "onCreate", "onDestroy", "onBind", "onUnbind",
            "onActivate", "onDeactivate", "onMount", "onUnmount"
        ]

    def read_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except Exception as e:
            logging.error(f"Error reading file: {e}")
            sys.exit(1)

    def parse_header_for_methods(self, header_content):
        method_presence = {method: False for method in self.mandatory_methods}
        for method in self.mandatory_methods:
            pattern = rf"\b{method}\b\s*\([^)]*\)"
            if re.search(pattern, header_content):
                method_presence[method] = True
        missing_methods = [method for method, present in method_presence.items() if not present]
        return "OK" if not missing_methods else f"Missing methods: {', '.join(missing_methods)}"

    def parse_xml_for_method_signatures(self, xml_content):
        root = ET.fromstring(xml_content)
        method_signatures = {}
        for method in root.findall('.//method'):
            method_name = method.get('name')
            params = [(param.get('type'), param.get('name')) for param in method.findall('.//param')]
            method_signatures[method_name] = params
        return method_signatures

    def parse_published_methods(self, header_content):
        # from documentation this is roughly where functions we are lookin for are
        start_marker = "// Published custom methods"
        end_marker = "protected:"
        start_idx = header_content.find(start_marker)
        end_idx = header_content.find(end_marker, start_idx)
        published_section = header_content[start_idx:end_idx]

        # regex
        published_methods = re.findall(r'\b\w+\s+\w+\s*\([^)]*\)', published_section)
        if published_methods[0] == "the findObjects()": published_methods = published_methods[1:]
        return published_methods

    @staticmethod
    def parse_header_param(header_param):
        # remove reference symbol '&' and split the parameter
        parts = header_param.replace('&', '').split()
        
        # handling cases like 'std::string' and kr2_program_api::
        if len(parts) >= 2 and '::' in parts[0]:
            type_part = parts[0].split('::')[-1]
        else:
            type_part = parts[0] if parts else ''

        name_part = parts[-1] if len(parts) > 1 else ''
        return type_part, name_part
    
    def compare_method_signatures(self, header_content, xml_method_signatures):
        comparison_results = {}
        for method_name, xml_params in xml_method_signatures.items():
            pattern = rf"{method_name}\s*\(([^)]*)\)"
            match = re.search(pattern, header_content)
            if match:
                header_params_str = match.group(1)
                header_params = [param.strip() for param in header_params_str.split(',') if param.strip()]

                if len(header_params) != len(xml_params):
                    comparison_results[method_name] = f"Parameter count mismatch: Expected {len(xml_params)}, found {len(header_params)}"
                    continue
                mismatch = False
                mismatch_details = []
                for header_param, xml_param in zip(header_params, xml_params):
                    header_param_type, header_param_name = self.parse_header_param(header_param)

                    if header_param_type != xml_param[0] or header_param_name != xml_param[1]:
                        mismatch = True
                        mismatch_details.append(f"Header: {header_param_type} {header_param_name}, XML: {xml_param[0]} {xml_param[1]}")

                if mismatch:
                    comparison_results[method_name] = f"Signature mismatch:{' '.join(mismatch_details)}"
                else:
                    comparison_results[method_name] = "Signatures match"
            else:
                comparison_results[method_name] = "Method not found in header"
        return comparison_results

    def run(self):
        # read xml/.h
        header_content = self.read_file(self.header_file)
        xml_content = self.read_file(self.xml_file)

        # mandatory methods check
        mandatory_check = self.parse_header_for_methods(header_content)
        logging.info(f"Mandatory method check: {mandatory_check}")

        # extract xml methods
        xml_signatures = self.parse_xml_for_method_signatures(xml_content)
        logging.info("XML method signatures:")
        for method, params in xml_signatures.items():
            logging.info(f"   {method}: {', '.join([f'{ptype} {pname}' for ptype, pname in params])}")
        
        # extract .h published methods
        published_methods = self.parse_published_methods(header_content)
        logging.info(f"Header published metods detected:")
        for method in published_methods:
            logging.info(f"   {method}")
    
        # xml and .h lenght check
        logging.info(f"Methods count: XML({len(xml_signatures)}), .h({len(published_methods)}) - {'OK' if len(xml_signatures) == len(published_methods) else 'FAIL'}")

        # compare xml against .h methods
        comparison_results = self.compare_method_signatures(header_content, xml_signatures)
        logging.info("Comparison results:")
        for method, result in comparison_results.items():
            logging.info(f"   {method}: {result}")

def setup_arg_parser():
    parser = ArgumentParser(description="Validate method signatures between header and XML files.")
    parser.add_argument("header_file", help="Path to the header file.")
    parser.add_argument("xml_file", help="Path to the XML file.")
    return parser

def main():
    # args
    parser = setup_arg_parser()
    args = parser.parse_args()

    # script run
    validator = Validator(args.header_file, args.xml_file)
    validator.run()

if __name__ == "__main__":
    main()

# TODO:
#   - Improve on logging readability
#
# Notes:
# I am using regex and not something like pycparser.
# If this solution proves not great, i will rewrite it.
# My published function finder hangs on the idea that .h file is correctly written as on test case.
# In other words if start or end marker fails, the script would fail, therefore:
# I am checking xml against another regex that should not fail
# 
# Function to check structure of xml as whole is missing, documentation says to include mounting, but in test case
# its missing. If required and more details i will provide one
