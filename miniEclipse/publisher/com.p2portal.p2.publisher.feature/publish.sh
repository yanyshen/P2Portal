# check REPO_HOME variable
#if [ -z ${REPO_HOME} ]
#then
#	echo "REPO_HOME variable must be set before publishing"
#	exit
#fi
#echo ${REPO_HOME}

# call publisher with IDE specific program arguments
#export ide=`sed "s#REPO_HOME#${REPO_HOME}#g" -f demo.ini`
export ide=`sed "s#REPO_HOME#$(pwd)/../../../../../../../../..#g" -f demo.ini`
echo ${ide}
./publisher ${ide}
