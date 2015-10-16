Eclipse Plugin Repository Portal
==================
##Overview

Eclipse Plugin Repository Portal is a repositories management system, which provides a web interface for the end users to manage Eclipse Plugins and provide update sites to end users. It helps developer, tester and end customer to quickly work togther. It has the following features:

  * Centralized Management
  
  * Visualized Management Page
  
  * Simplified Process and Operation
  
  * Reliable Release Process

With this system, the user can do the following operation through the graphic user interface.
* Create a repository by publishing or mirroring;
* Rollback a repository to a previous version;
* Make a composite;
* View operation history;
* Edit category for a repository;
* Edit/delete a composite;
* Edit the information of an existing repository;
* Add/delete a folder;
![operations](https://github.com/eBay/P2Portal/raw/master/images/operation.png)
In this way, the end user can be free from manual operations which have been proven error prone and time consuming. Eclipse Plugin Repository Portal will play a key role on making the process more efficient and stable with high quality.


## Use Scenario

![prcess](https://github.com/eBay/P2Portal/raw/master/images/process.png)


##Glossary And Acronyms

* Category - A term which is used to describe what features a repository provides;
* Composite - A term which is used to aggregate several eclipse plugins together;
* Repo -  Repository;
* Site, Repository Site - A term which is used to aggregate eclipse features, plugins, composite of different development phase for one project. For example, for RIDE, we have dev site, qa site, release site

  Plese refer to [Use Cases](https://github.com/eBay/P2Portal/wiki/Use-Cases)

##Architecture

![architecture](https://github.com/eBay/P2Portal/raw/master/images/architeture.png)

##System Requirements

Eclipse Plugin Repository Portal runs on Windows(64bit) and Linux (64 Bit).

##Installation Guide

1．Build Eclipse Plugin Repository Portal
    
    For Linux:

    # Ensure apt-get is up to date.
    $ sudo apt-get update
    
    # Install JDK
    $ sudo apt-get install openjdk-7-jdk
    
    # Install Git
    $ sudo apt-get install git

    # Setup workspace
    $ cd /
    $ sudo git clone git@github.com:eBay/P2Portal.git
    
    # Install Python libs
    $ sudo apt-get install make build-essential zlib1g-dev libbz2-dev libreadline-dev
    $ sudo apt-get install sqlite3 libsqlite3-dev
    $ sudo apt-get install libssl-dev
    
    
    # Build Python, Download Python2.7.5 from http://www.python.org/download/
    $ sudo wget https://www.python.org/ftp/python/2.7.5/Python-2.7.5.tgz
    $ sudo tar zxf Python-2.7.5.tgz
    $ sudo cd Python-2.7.5
    # sudo build 
    $ sudo ./configure --prefix=/P2Portal/python
    $ sudo make
    $ sudo make install
    
    # Install easy_install
    $ sudo apt-get install python-setuptools
    
    # Install Django 
    $ sudo easy_install https://pypi.python.org/packages/source/D/Django/Django-1.4.1.tar.gz
    
    # Install djangorestframework
    $ sudo easy_install https://pypi.python.org/packages/source/d/djangorestframework/djangorestframework-0.3.1.tar.gz
    
    # Install async
    $ sudo  easy_install https://pypi.python.org/packages/source/a/async/async-0.6.1.tar.gz
    
    # Install smmap
    $ sudo easy_install https://pypi.python.org/packages/source/s/smmap/smmap-0.8.2.tar.gz
 
    # Install GitPython
    $ sudo easy_install https://pypi.python.org/packages/source/G/GitPython/GitPython-0.3.2.RC1.tar.gz
    
    
    # Build MiniEclipse 
    
    
    #Download
    a) Download eclipse  4.3.2 linux from https://www.eclipse.org/downloads/packages/eclipse-standard-432/keplersr2   
    
    b) extract and start Eclipse kepler                               
    
    c) Git clone Eclipse Plugin Repository Portal repository 
    
    d) Import features and plugins from miniEclipse folder via File->Import->Import existing projects                           
    # Export
    To export miniEclipse for multiple platforms, you need go through below step: 
    
    a) Select miniEclipse.target, open it, and click "Set as Target Platform".      
    
                                                                                                                             b) Select miniEclipse.product, right click Export->Eclipse Product,
                                                                                                                                You will see that the "Export for multiple platforms"     
   
    c) checkbox is available. Select this option, Click next, Select the platforms you wish to export, click finish.        
   
    # Apply
    a) Change folder name from eclipse to miniEclipse.                                                                            
    b) Copy miniEclipse folder C:/P2Portal.
 
    For Windows:

    # Install JDK
      Please refer http://docs.oracle.com/javase/7/docs/webnotes/install/windows/jdk-installation-windows.html
    
    
    # Install Git, download installer from http://git-scm.com/download/win and install it
      Add Git installation path into system path variable.

    # Setup workspace
    > cd C:
    > git clone git@github.corp.ebay.com:P2Portal/P2Portal.git
    
    # Install Python libs
      Download Python2.7.5 Windows x86-64 from http://www.python.org/download/ and install. 
      Add python installation path (e.g.c:\Python27) to your system path variable.
      Copy python27.dll from C:\Windows\SysWOW64 to python install path.
  
    # Download setuptools
      Download and execute this script: http://peak.telecommunity.com/dist/ez_setup.py

    # Install Django 
    > easy_install https://pypi.python.org/packages/source/D/Django/Django-1.4.tar.gz 
    
    # Install djangorestframework
    > easy_install https://pypi.python.org/packages/source/d/djangorestframework/djangorestframework-0.3.1.zip
    
    # Install async
    > easy_install https://pypi.python.org/packages/source/a/async/async-0.6.1.tar.gz
    
    # Install smmap
    > easy_install https://pypi.python.org/packages/source/s/smmap/smmap-0.8.2.tar.gz
    
    # Install gitdb
    > easy_install https://pypi.python.org/packages/source/g/gitdb/gitdb-0.5.3.tar.gz
    # Install GitPython
    > easy_install https://pypi.python.org/packages/source/G/GitPython/GitPython-0.3.2.RC1.tar.gz 
    
    # Build MiniEclipse 	
	    
    #Download
    a) Download eclipse  4.3.2 windows 64 from https://www.eclipse.org/downloads/packages/eclipse-standard-432/keplersr2   
    b) extract and start Eclipse kepler                               
    
    c) Git clone Eclipse Plugin Repository Portal repository 
    
    d) Import features and plugins from miniEclipse folder via File->Import->Import existing projects                           
    # Export
    To export miniEclipse for multiple platforms, you need go through below step: 
    
    a) Select miniEclipse.target, open it, and click "Set as Target Platform".      
 
    b) Select miniEclipse.product, right click Export->Eclipse Product,  You will see that the "Export for multiple platforms" checkbox is available. Select this option, Click next, Select the platforms you wish to export, click finish.        
   
    # Apply
    a) Change folder name from eclipse to miniEclipse.                                                                            
    b) Copy miniEclipse folder C:/P2Portal.
     
 2．Run a demo:

    a) Change portal.conf field "location" to a absolute path.
    b)Run a configure script demo-pre-cfg.sh
       This file is under the folder of /P2Portal/demo/. Double click it and choose “Run in Terminal”.
       You will be asked to create a superuser. Choose Yes. Input username, email and password according to the tips.
       The username and password will be used to log in the admin page. You can also use it to log in the Eclipse Plugin Repository Portal.
    c) Start a server for Eclipse Plugin Repository Portal
         cd /P2Portal/portal
         python manage.py runserver <port> like 8081
    d) Start a HTTP File Server
        cd /P2Portal/update-sites
        python -m SimpleHTTPServer
    e) Access the system
       Access Eclipse Plugin Repository Portal by http://localhost:<port>/
       Access admin by http://localhost:<port>/admin.

3．Set up a production environment

    a) Configure repository location and site root path in /P2Portal/product/portal.conf 
        The content in this file is as follows:
        {
            "REPOSITORY_SITES": {
                "<site-name>": {
                    "hidden": false,
                    "location": "/P2Portal/update-sties/<site-name>",
                    "update_site": "<site-name>/"
                },
                "<site-name2>": {
                    "hidden": false,
                    "location": "/P2Portal/update-sties/<site-name2>",
                    "update_site": "<site-name2>/",
               
            },
            "SITE_PATH_ROOT": "update-sites",
            "SITE_URL_ROOT": "http://localhost:<port>/"
        }
      Property
     
      <site-name>	The site’s name. You can modify it by your requirement. For example, "RELEASE"
      
      location	Specify the path of the repository. It can be either an absolute path. Required
      
      update_sites Specify the url through with one can access the repository’s files in the way of HTTP File. Required
      hide	Indicate whether a repository site can be seen in Eclipse Plugin Repository Portal or not. Not necessary.
      
      SITE_PATH_ROOT	Specify the path that will contain the new created sites. If it’s a relative path, 
      the system will consider it as <install_path>/<SITE_PATH_ROOT>. Required and Unique.
      
      "SITE_URL_ROOT"	Specify the url through which you can access <SITE_PATH_ROOT> in the way of HTTP File. 
      Required and Unique.
      
      Tips: The “SITE_PATH_ROOT” and locations of repository sites must be configured in a certain HTTP File Server.  
      
      Please make sure that we can access them through urls specified in “SITE_URL_ROOT” and “update_site”.
    b)Run product-pre-cfg.sh to make portal.conf take effect.
      You will be asked to create a superuser. Choose Yes. Input username, email and password according to the tips.  
      
      The username and password will be used to log in the admin page. You can also use it to log in the Eclipse Plugin Repository Portal.    

	  By default, the target platform to run Eclipse Plugin Repository Portal is in windows. If you want to run it on other OS, you need to export MiniEclipse for other OS and modify the scripts "cp -a win32.win32.x86_64/eclipse/. ../miniEclipse" to replace "win32.win32.x86_64" to the one you export.
	  
    c)Start a server for Eclipse Plugin Repository Portal.
      cd <install_path>/portal
      python manage.py runserver <port> like 8081
         
    d)Start a server for HTTP File Server.
      You can use the simple http server provided by python
      cd <your-update-sites>
      python -m SimpleHTTPServer
                 
    e)Access Eclipse Plugin Repository Portal
      Access Eclipse Plugin Repository Portal by http://localhost:<port>/.
      Access admin by http://localhost:<port>/admin.

## More Documents 

[Setup Developing Environment for Eclipse Plugin Repository Portal](https://github.com/eBay/P2Portal/wiki/Setup-Developing-Environment-for-P2Portal)

[Use Cases ](https://github.com/eBay/P2Portal/wiki/Use-Cases)

