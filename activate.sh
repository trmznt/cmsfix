# example of activate.sh
# to activate: source activate.sh

_script="$(readlink -f ${BASH_SOURCE[0]})"

## Delete last component from $_script ##
_mydir="$(dirname $_script)"

#set this to python3 virtual env activate
source ${_mydir}/../../bin/activate

#set this to configuration file
export CMSFIX_CONFIG=${_mydir}/development.ini

#set this for additional paths
export PATH=${_mydir}/libexec:${PATH}
