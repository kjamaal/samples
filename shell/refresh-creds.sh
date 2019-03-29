#!/bin/zsh

usage() { echo -e "Usage: $1 [-h] [-p profile name] [-m mfa arn] [-d duration] [-t mfa token]\n\n \
DESCRIPTION: Updates ~/.aws/credentials with sts temporary credentials using MFA. \n \
NOTE: expects that ~/.aws/credentials contains a profile named 'default' as the first entry e.g. [default] \n\n \
OPTIONS: \n \
-p profile to update \n \
-m mfa arn, default will use the first mfa_serial entry in ~/.aws/credentials \n \
-d duration in seconds, default is aws default \n \
-t mfa token \n \
-h this help" 1>&2; exit 1; }

while getopts ":p:m:d:t:h:" opt; do
    case "${opt}" in
        p)  
            profile=${OPTARG}
            ;;
        m)  
            mfa=${OPTARG}
            ;;
        d)  
            duration=${OPTARG}
            ;;
        t)
            token=${OPTARG}
            ;;
        *)
            usage $0
            ;;
    esac
done

if [ -z "$profile" ] || [ -z "$token" ]; then
  echo "-p and -t are required" 1>&2 
  usage
  exit 1
fi

creds_file="$HOME/.aws/credentials"
default_access_key=$(grep -A 2 -e "\[default\]" $creds_file | grep aws_access_key_id | awk -F = '{ print $2 }' | tr -d " " )
default_secret_key=$(grep -A 2 -e "\[default\]" $creds_file | grep aws_secret_access_key | awk -F = '{ print $2 }' | tr -d " " )
cred_count="0"

if [[ $mfa != arn* ]] || [[ -z $mfa ]]; then
  if [ -f $creds_file ]; then    
    mfa=$(grep -m 1 '^mfa_serial' $creds_file | awk -F = '{ print $2 }' | tr -d " ")
  else
    echo "No credentials file at ${creds_file}. Try running aws configure." 1>&2 
  fi   
fi

creds=$(aws sts get-session-token --serial-number $mfa --token-code $token)

while [ $cred_count -lt 3 ]
do
  case "${cred_count}" in 
    0)
        accesskey=$(echo $creds | grep "AccessKeyId" | awk '{ print $2 }' | tr -d "\",")
        ;;
    1)
        secretaccess=$(echo $creds | grep "SecretAccessKey" | awk '{ print $2 }' | tr -d "\",")
        ;;
    2)
        sessiontoken=$(echo $creds | grep "SessionToken" | awk '{ print $2 }' | tr -d "\",")
        ;;
  esac
  cred_count=$[$cred_count+1]
done

sed -i "" "/${default_access_key//\//\\/}/! s/^aws_access_key_id.*/aws_access_key_id = ${accesskey//\//\\/}/" $creds_file
sed -i "" "/${default_secret_key//\//\\/}/! s/^aws_secret_access_key.*/aws_secret_access_key = ${secretaccess//\//\\/}/" $creds_file
sed -i "" 's/^aws_session_token.*/aws_session_token = '"${sessiontoken//\//\\/}"'/' $creds_file