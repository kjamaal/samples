#!/bin/bash

usage() { echo "Usage: $0 [-t some test parameter] [-p some other test parameter]" 1>&2; exit 1; }

while getopts ":t:p:" opt; do
    case "${opt}" in
        t)
            test=${OPTARG}
            ;;
        p)
            param=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done

#Make -t required
if [ -z "$test" ]; then
    echo "-t is required" 1>&2
    usage
    exit 1
fi

echo "$test"
echo "$param"
