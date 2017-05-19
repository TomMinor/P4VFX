import os
import sys
import platform
import shutil
import argparse


class App(object):
    def __init__(self):
        self.cwd = os.path.dirname(os.path.realpath(__file__))

    def getPreferences(self):
        pass

    def install(self):
        pass

    def install_p4python(self, dest):
        # @ToDo set this up to sort out the /Maya, /Nuke subfolders under apidir

        if not os.path.exists(dest):
            os.makedirs(dest)

        apiplatform = platform.system().lower()
        apidir = os.path.join(self.cwd, os.path.join('P4API', apiplatform))

        if platform.system() == 'Windows':
            p4lib = 'P4API.pyd'
        else:
            p4lib = 'P4API.so'

        logSymlink(os.path.join(apidir, p4lib), os.path.join(dest, p4lib))
        logSymlink(os.path.join(apidir, 'P4.py'), os.path.join(dest, 'P4.py'))


    def install_perforce_module(self, dest):
        if not os.path.exists(dest):
            os.makedirs(dest)

        moduledir = os.path.realpath(os.path.join(self.cwd, 'src/perforce'))

        logSymlink(moduledir, os.path.join(dest, 'perforce'))



class Maya(App):
    def getPreferences(self):
        """
            This returns the non-versioned Maya path, as we should be fairly version agnostic and work with any Maya
        """
        if os.environ.get('MAYA_APP_DIR'):
            maya_app_dir = os.environ['MAYA_APP_DIR']
            return maya_app_dir

        if platform.system() == 'Windows':
            if os.environ.get('HOME'):
                home = os.environ['HOME']
            else:
                home = os.environ['USERPROFILE']
            return os.path.realpath(os.path.join(home, 'Documents/maya'))

        elif platform.system() == 'Linux':
            return os.path.expanduser('~/maya')

        elif platform.system() == 'Darwin':
            os.path.expanduser('~/Library/Preferences/Autodesk/maya')


    def install(self):
        # Setup Maya
        maya_scripts = os.path.join(self.getPreferences(), 'scripts')
        maya_plugins = os.path.join(self.getPreferences(), 'plug-ins')
        maya_plugin_src = os.path.realpath(os.path.join(self.cwd, 'src/AppPlugins/P4Maya.py'))
        maya_plugin_dst = os.path.join(maya_plugins, os.path.basename(maya_plugin_src))
        self.install_p4python(maya_scripts)
        self.install_perforce_module(maya_scripts)

        if not os.path.exists(maya_plugin_dst):
            os.makedirs(maya_plugin_dst)
        logSymlink(maya_plugin_src, maya_plugin_dst)


class Nuke(App):
    def getPreferences(self):
        if platform.system() == 'Windows':
            if os.environ.get('HOME'):
                home = os.environ['HOME']
            else:
                home = os.environ['USERPROFILE']
            return os.path.join(home, '.nuke')

        elif platform.system() == 'Linux':
            return os.path.expanduser('~/.nuke')

        elif platform.system() == 'Darwin':
            return os.path.expanduser('~/.nuke')

    def install(self):
        userprefs = self.getPreferences()

        nuke_plugin_src = os.path.realpath(os.path.join(self.cwd, 'src', 'AppPlugins', 'P4Nuke'))
        nuke_init_py_src = os.path.join(nuke_plugin_src, 'init.py')
        nuke_menu_py_src = os.path.join(nuke_plugin_src, 'menu.py')

        nuke_plugin_dst = os.path.join(userprefs, 'P4Nuke')
        nuke_init_py_dst = os.path.join(nuke_plugin_dst, 'init.py')
        nuke_menu_py_dst = os.path.join(nuke_plugin_dst, 'menu.py')

        if not os.path.exists(nuke_plugin_dst):
            os.makedirs(nuke_plugin_dst)

        self.install_p4python(nuke_plugin_dst)
        self.install_perforce_module(nuke_plugin_dst)

        logSymlink(nuke_init_py_src, nuke_init_py_dst)
        logSymlink(nuke_menu_py_src, nuke_menu_py_dst)


class Houdini(App):
    def getPreferences(self):
        if platform.system() == 'Windows':
            if os.environ.get('HOME'):
                home = os.environ['HOME']
            else:
                home = os.environ['USERPROFILE']
            return os.path.join(home, 'Documents', 'houdini16.0')

        elif platform.system() == 'Linux':
            return os.path.expanduser('~/Documents/houdini16.0')

        elif platform.system() == 'Darwin':
            return os.path.expanduser('~/Documents/houdini16.0')

    def install(self):
        userprefs = self.getPreferences()

        hou_plugin_src = os.path.realpath(os.path.join(self.cwd, 'src', 'AppPlugins', 'P4Houdini'))
        hou_pythonrc_py_src = os.path.join(hou_plugin_src, 'python2.7libs', 'pythonrc.py')

        hou_plugin_dst = os.path.join(userprefs, 'python2.7libs', 'P4Houdini')
        hou_pythonrc_py_dst = os.path.join(userprefs, 'python2.7libs', 'pythonrc.py')

        if not os.path.exists(hou_plugin_dst):
            os.makedirs(hou_plugin_dst)

        self.install_p4python(hou_plugin_dst)
        self.install_perforce_module(hou_plugin_dst)

        logSymlink(hou_pythonrc_py_src, hou_pythonrc_py_dst)




def setEnvironmentVariable(key, value):
    if platform.system() == 'Windows':
        os.system('setx %s %s' % (key,value))
    else:
        with open(os.path.expanduser('~/.bash_profile')) as f:
            f.write('export %s=%s' % (key,value))

def logSymlink(src, dst):
    if not os.path.exists(src):
        raise IOError('%s doesn\'t exist' % src)

    if os.path.exists(dst):
        print '%s exists, unlinking...' % dst
        try:
            if os.path.exists(dst):
                if os.path.islink(dst):
                    os.unlink(dst)
                else:
                    if os.path.isdir(dst):
                        os.rmdir(dst)
                    else:
                        os.remove(dst)
                        # shutil.rmtree(dst)
        except OSError as e:
            print 'Symlink error: %s' % e
            return

    print 'Linking %s to %s...' % (src, dst)
    os.symlink(src, dst)


def setupCommandLineArgs():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-p', '--p4port', help='The Perforce server IP saved to P4CONFIG, e.g. ssl:12.34.567.8:1666')

    parser.add_argument(
        '-c', '--p4config', help='The P4CONFIG file to write to (default is \'~/.p4config\')', default='~/.p4config')
    parser.add_argument(
        '-e', '--p4editor', help='Override the editor used by Perforce, highly recommended to avoid hangs in GUI apps')

    return parser.parse_args()


def setup(args):
    if platform.system() == 'Windows':
        import ctypes

        # Unfortunately this method doesn't work with junctions properly,
        # Python2.7 can't import folders symlinked using this method
        # 
        # def symlink_ntfs(source, link_name):
        #     source = source.replace('\\', '/')
        #     link_name = link_name.replace('\\', '/')

        #     kdll = ctypes.windll.LoadLibrary("kernel32.dll")
        #     kdll.CreateSymbolicLinkW(unicode(link_name), unicode(source), os.path.isdir(source))

        # For a simple install script we can hopefully rely on mklink being installed.
        # If it's not, you would have to make do with simply copying the files instead
        def mklink(source, link_name):
            from subprocess import check_output, CalledProcessError 
            try:
                if os.path.isdir(source):
                    check_output("mklink /J %s %s" % (link_name, source), shell=True)
                else:
                    check_output("mklink %s %s" % (link_name, source), shell=True)
            except CalledProcessError as e:
                print e

        def is_admin():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False

        # If we're on Windows, the python symlink function isn't available
        os.symlink = mklink

        # If this prompt isn't an admin prompt, Windows won't let us symlink :(
        if not is_admin():
            print "Warning: This prompt isn't elevated, not possible to symlink files. Do a simple copy instead? [Y/N]"
            sys.stdout.flush()

            yes = set(['yes', 'y', 'ye', ''])
            no = set(['no', 'n'])
            choice = raw_input().lower()
            if choice in yes:
                print 'Copying instead of linking...'
                os.symlink = shutil.copyfile
            else:
                print 'Aborting.'
                sys.exit(1)





def install_environment(args):
    # # Perforce for Maya relies on these variables being set in some form or another
        # # Setup config (Bash)
        # echo "export P4CONFIG=$_P4CONFIGPATH" >> ~/.profile

    p4config = os.path.realpath(os.path.expanduser(args.p4config))

    p4configpath, p4configfile = os.path.split(p4config)
    if not os.path.exists(os.path.dirname(p4configpath)):
        try:
            os.makedirs(os.path.dirname(p4configpath))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    if not os.path.exists(p4config):
        open(p4config, 'a').close()

    # if not os.environ.get('P4CONFIG'):
    #     setEnvironmentVariable('P4CONFIG', p4config)

    try:
        contents = open(p4config).read()
    except IOError as e:
        print e
        return

    with open(p4config, 'w') as f:
        if not 'P4PORT' in contents:
            f.write('P4PORT=%s' % args.p4port)

        if args.p4editor and not 'P4EDITOR' in contents:
            f.write('P4EDITOR=%s' % args.p4editor)
    



def install(args):
    apps = [ 
                # Maya(),
                Nuke(),
                Houdini()
            ]
    for app in apps:
        app.install()

    # Configure P4CONFIG etc
    # if args.p4config:
    #     install_environment(args)


if __name__ == '__main__':
    args = setupCommandLineArgs()
    setup(args)
    install(args)

    print 'Done!'
