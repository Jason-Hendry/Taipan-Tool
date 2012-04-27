#!/usr/bin/python

import argparse,sys,os,re,subprocess

def color(string,color=33):
    return '\033['+str(color)+';1m' + string + '\033[0m'

def getModules():
    modpath = getModulePath();
    if(modpath == None):
      return [];
    modules = [];
    if(os.path.isdir(os.path.join(modpath,'core'))):
        modules.append('core');
    
    if(os.path.isdir(os.path.join(modpath,'optional'))):
        optional = os.listdir(os.path.join(modpath,'optional'))
        for o in optional:
            if o != ".svn":
                modules.append(os.path.join('optional',o))

    if(os.path.isdir(os.path.join(modpath,'custom'))):
        custom = os.listdir(os.path.join(modpath,'custom'))
        for c in custom:
            if c != ".svn":
                modules.append(os.path.join('custom',c))

    return modules

Gmodpath = None;

def getModulePath():
    global Gmodpath;
    if(Gmodpath != None):
      return Gmodpath;
    cwd = os.getcwd()
    if(re.match("[\\/]include$",cwd)):
        if(os.path.isdir(os.path.join(cwd,'modules'))):
            Gmodpath = os.path.join(cwd,'modules')
            return Gmodpath;
    elif(re.match("^(.*[\\/]include[\\/]modules).*$",cwd)):
        m = re.match("^(.*[\\/]include[\\/]modules).*$",cwd);
        Gmodpath = m.group(0);
        return Gmodpath;
    elif(os.path.isdir(os.path.join(cwd,'include','modules'))):
        Gmodpath = os.path.join(cwd,'include','modules');
        return Gmodpath;
    return None;
    
def getVersionExternals(module):
    modpath = getModulePath();
    if(modpath != None):
       extdir = os.path.dirname(os.path.join(modpath,module));
       svn = subprocess.Popen(['svn','propget','svn:externals',extdir],stdout=subprocess.PIPE);
       externals = svn.communicate()[0];
       m = re.search(module+"/(.*)",externals)
       if(m == None):
           return 'N/A'       
       return m.group(1);
    return 'N/A';
    
def getVersionWorking(module):
    modpath = getModulePath();
    if(modpath != None):
       moddir = os.path.join(modpath,module);
       svn = subprocess.Popen(['svn','info',moddir],stdout=subprocess.PIPE);
       info = svn.communicate()[0];
       m = re.search("URL.*/([^/]*)\n",info)
       if(m == None):
           return 'N/A'       
       return m.group(1);
    return 'N/A';
    
def getVersionLatest(module):
    svndir = 'svn://svn.pre/taipan/modules/'+module;
    svn = subprocess.Popen(['svn','ls',svndir],stdout=subprocess.PIPE);
    svnls = svn.communicate()[0];
    
    versions = []
    for i in re.split("\n",svnls):
        if(re.search('[a-z]',i)): # skip all branches with letters
            continue
        if(i == ''): # skip blank
            continue
        v = [i.strip('/')];
        for j in (i.strip('/')+'.0').split('.'):
            v.append(int(j))
        versions.append(v)

    if(versions == []):
        return 'N/A'

    s = sorted(versions,key=lambda versions: versions[3]); 
    s = sorted(s,key=lambda versions: versions[2]); 
    s = sorted(s,key=lambda versions: versions[1]); 
    
    return s[-1][0]

def getVersion(module,version_type):
    if(version_type == 'externals'):
        return getVersionExternals(module)
    elif(version_type == 'working'):
        return getVersionWorking(module)
    elif(version_type == 'latest'):
        return getVersionLatest(module);
    else:
        return "(E:"+color(getVersionExternals(module))+' W:'+getVersionWorking(module)+' L:'+getVersionLatest(module)+')'

def AddModule(module,version):
    if(version):
        print "Adding module "+module+" v:"+version+"..."
    else:
        print "Searching for latest version of "+module+"..."

def getModuleType(module):
    modpath = getModulePath()
    if(os.path.isdir(os.path.join(modpath,'custom',module))):
        return os.path.join('custom',module);
    if(os.path.isdir(os.path.join(modpath,'optional',module))):
        return os.path.join('optional',module);
    if(os.path.isdir(os.path.join(modpath,module))):
        return module;

def hasModule(module):
    if(getModuleType(module) == None):
        return False
    return True

def moduleName(module):
    return os.path.basename(module)

def checkDependencies(module):
    modpath = os.path.join(getModulePath(),module);
    if(os.path.isdir(modpath)):
        info = open(os.path.join(modpath,moduleName(module)+'.info'));
        print 'Checking Dependencies...'
        while(True):
            line = info.readline()
            if(line == ''):
                break
            
            core = re.match('core: (.*)',line)
            other = re.match('\s*(.*)/(.*)',line)
            if(core):
                print line.strip("\n")+' '+getVersion('core',None)
            elif(other):
                if(hasModule(other.group(1))):
                    print line.strip("\n")+' '+getVersion(getModuleType(other.group(1)),None)
                else:
                    print line.strip("\n")+' - Not installed'
            else:
                print line.strip("\n")    
            
        

def main():
    def version(args):
        if(args.module):
            print getModuleType(args.module)+' versions\n  SVN:Externals: '+getVersion(getModuleType(args.module),'externals')+'\n  Working Copy: '+getVersion(getModuleType(args.module),'working')+'\n  Latest (repo): '+getVersion(getModuleType(args.module),'latest')
        else:
            for m in getModules():
                print m+' v: '+getVersion(m,None)
                
    def check(args):
        version(args)
        print ''
        checkDependencies(getModuleType(args.module));

    def add(args):
        if(args.module):
            AddModule(args.module,args.version);

    def list(args):
        for m in getModules():
            print m+"\n";

    parser = argparse.ArgumentParser(description='Taipan Tool')
    subparsers = parser.add_subparsers(help='Command help')
 
    parser_version = subparsers.add_parser('version')
    parser_version.add_argument('module',nargs="?");
    parser_version.set_defaults(func=version)    

    parser_check = subparsers.add_parser('check')
    parser_check.add_argument('module');
    parser_check.set_defaults(func=check)    

    parser_add = subparsers.add_parser('add')
    parser_add.add_argument('module', help="Module name eg (cms, gallery-admin, etc)");
    parser_add.add_argument('-v', dest='version', metavar="Version", help="Module Version number eg (1.0, 2.3.1... trunk)");
    parser_add.set_defaults(func=add)    

    parser_list = subparsers.add_parser('list')
    parser_list.set_defaults(func=list)    

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
