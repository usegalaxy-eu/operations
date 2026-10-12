"""Fetch tool requirements and resolve container identifiers.

WARNING: This is a stub script, it has not been finished nor reviewed.
"""

import argparse
import requests
import sys
import time
import os
import subprocess
import re
import concurrent.futures


def get_tool_requirements(tool_id, cookie=None):
    """
    Fetches the requirements for a tool using the build endpoint.
    """
    url = f"https://usegalaxy.eu/api/tools/{tool_id}/build"
    params = {
        "version": "latest",
        "tool_version": "latest"
    }

    headers = {}
    if cookie:
        headers['Cookie'] = cookie

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        return data.get('requirements', [])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {tool_id}: {e}", file=sys.stderr)
        try:
            if e.response is not None:
                # Truncate potentially long error messages
                print(f"Response: {e.response.text[:200]}", file=sys.stderr)
        except:
            pass
        return None


def resolve_container(resolver_script, resolver_conf, requirements):
    """
    Calls the external container resolver script to get the container identifier.
    requirements is a list of strings like "name=canu version=2.3"
    """
    package_arg = ",".join(requirements)

    cmd = [resolver_script]
    if resolver_conf:
        cmd.extend(["--config", resolver_conf])

    cmd.extend(["--package", package_arg])

    try:
        # Run the script and capture output
        result = subprocess.run(cmd, capture_output=True, text=True,
                                check=True)
        output = result.stdout

        identifiers = []
        for line in output.splitlines():
            match = re.search(r"ContainerDescription\[identifier=(.*?),type=",
                              line)
            if match:
                identifiers.append(match.group(1))

        if identifiers:
            return identifiers[0]

        return "No container found"

    except subprocess.CalledProcessError as e:
        # Keeping stderr clean for the main thread, or we could print here.
        # Since this runs in a thread, logging to stderr is okay.
        print(f"Error running resolver script: {e}", file=sys.stderr)
        return "Resolver failed"
    except Exception as e:
        print(f"Error during resolution: {e}", file=sys.stderr)
        return "Resolution error"


def process_tool(tool_id, args):
    """
    Worker function to process a single tool.
    """
    requirements = get_tool_requirements(tool_id, args.cookie)

    req_list_formatted = []
    container_id = "N/A"

    if requirements is not None:
        if requirements:
            for req in requirements:
                name = req.get('name', 'unknown')
                version = req.get('version', 'unknown')
                req_list_formatted.append(f"name={name} version={version}")

            if args.resolver_script:
                container_id = resolve_container(args.resolver_script,
                                                 args.resolver_conf,
                                                 req_list_formatted)

            req_string = ", ".join(req_list_formatted)
            return f'{tool_id}, "{req_string}", {container_id}'
        else:
            # No requirements found
            return f'{tool_id}, "", N/A'
    else:
        # Error fetching requirements (already logged to stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Fetch tool requirements and resolve containers.")
    parser.add_argument("--input", default="tools.txt",
                        help="Input file containing tool IDs (one per line)")
    parser.add_argument("--cookie",
                        help="Cookie string for authentication (e.g. 'galaxysession=...')")
    parser.add_argument("--resolver-script",
                        help="Path to the container_resolvers.sh script")
    parser.add_argument("--resolver-conf",
                        help="Path to the container_resolvers_conf.yml")
    parser.add_argument("--threads", type=int, default=10,
                        help="Number of threads to use (default: 10)")
    parser.add_argument("--output", help="Output file to save results")

    args = parser.parse_args()

    input_path = args.input
    if not os.path.exists(input_path):
        # simple check if file exists, otherwise try to be smart about location relative to script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        potential_path = os.path.join(script_dir, args.input)
        if os.path.exists(potential_path):
            input_path = potential_path
        elif os.path.exists(os.path.join(script_dir, "..", args.input)):
            input_path = os.path.join(script_dir, "..", args.input)
        else:
            print(f"Error: Input file '{args.input}' not found.",
                  file=sys.stderr)
            sys.exit(1)

    print(f"Reading tools from: {input_path}", file=sys.stderr)

    try:
        with open(input_path, 'r') as f:
            tool_ids = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Found {len(tool_ids)} tools to process. Using {args.threads} threads.",
        file=sys.stderr)

    # Print header
    header = "tool_id, requirements, container_identifier"
    print(header)

    output_fh = None
    if args.output:
        try:
            output_fh = open(args.output, 'w')
            output_fh.write(header + '\n')
        except Exception as e:
            print(f"Error opening output file: {e}", file=sys.stderr)
            sys.exit(1)

    # Use ThreadPoolExecutor for concurrent processing
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.threads) as executor:
        future_to_tool = {executor.submit(process_tool, tool_id, args): tool_id
                          for tool_id in tool_ids}

        for future in concurrent.futures.as_completed(future_to_tool):
            tool_id = future_to_tool[future]
            try:
                result = future.result()
                if result:
                    print(result)
                    sys.stdout.flush()
                    if output_fh:
                        output_fh.write(result + '\n')
                        output_fh.flush()
            except Exception as exc:
                print(f'Exception processing {tool_id}: {exc}',
                      file=sys.stderr)

    if output_fh:
        output_fh.close()


if __name__ == "__main__":
    main()
