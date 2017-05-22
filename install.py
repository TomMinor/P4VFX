import os
import sys
import platform
import shutil
import argparse


class App(object):
    def __init__(self):
        self.cwd = os.path.dirname(os.path.realpath(__file__))

    def appendToFile(self, text, path):
        with open(path, 'a+') as f:
            lines = f.read()

            f.seek(0)
            if not text in lines:
                f.write('\n' + text)
            else:
                print '%s is initialized already, skipping setup' % path

    def getHome(self):
        if platform.system() == 'Windows':
            if os.environ.get('HOME'):
                home = os.environ['HOME']
            else:
                home = os.environ['USERPROFILE']
            return home

        elif platform.system() == 'Linux':
            return os.path.expanduser('~')

        elif platform.system() == 'Darwin':
            return os.path.expanduser('~')

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

        init_src = """
import nuke
nuke.pluginAddPath('./P4Nuke')
        """

        global_init_py = os.path.join(userprefs, 'init.py')
        self.appendToFile(init_src, global_init_py)


class Katana(App):
    def getPreferences(self):
        user_dir = os.getenv("KATANA_USER_RESOURCE_DIRECTORY")
        if user_dir:
            return user_dir

        if platform.system() == 'Windows':
            if os.environ.get('HOME'):
                home = os.environ['HOME']
            else:
                home = os.environ['USERPROFILE']
            return os.path.join(home, '.katana')

        elif platform.system() == 'Linux':
            return os.path.expanduser('~/.katana')

        elif platform.system() == 'Darwin':
            return os.path.expanduser('~/.katana')

    def install(self):
        userprefs = self.getPreferences()

        katana_plugin_src = os.path.realpath(os.path.join(self.cwd, 'src', 'AppPlugins', 'P4Katana'))
        katana_init_py_src = os.path.join(katana_plugin_src, 'init.py')

        katana_plugin_dst = os.path.join(userprefs, 'P4Katana')
        katana_init_py_dst = os.path.join(userprefs, 'init.py')

        if not os.path.exists(katana_plugin_dst):
            os.makedirs(katana_plugin_dst)

        self.install_p4python(katana_plugin_dst)
        self.install_perforce_module(katana_plugin_dst)

        logSymlink(katana_init_py_src, katana_init_py_dst)

#         init_src = """
# import sys
# import traceback
# import nuke
# import perforce

# import logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# try:
#     logger.info('Adding Perforce Menu...')
#     perforce.init()
# except Exception as e:
#     logger.error( 'Failed to load Perforce for Katana: %s\n' % e )
#     logger.error( traceback.format_exc() )
#         """

#         global_init_py = os.path.join(userprefs, 'init.py')
#         self.appendToFile(init_src, global_init_py)


class Houdini(App):
    def getPreferences(self):
        homedir = self.getHome()
        
        prefs = []

        # Really dodgy way of checking for the houdini version by counting down until we find valid houdinis
        # Something tells me this won't be used in houdini 31, but who knows
        for x in xrange(30, 0, -1):
            versions = [x + (float(y) / 10) for y in range(0, 10)]
            for v in versions:
                houdiniprefs = os.path.join(homedir, 'Documents', 'houdini%s' % (v))
                if os.path.exists(houdiniprefs):
                    prefs.append(houdiniprefs)

        return prefs

        

    def install(self):
        userprefs = self.getPreferences()
        if not userprefs:
            print 'Can\'t find a Houdini preferences directory.'
            return

        hou_plugin_src = os.path.realpath(os.path.join(self.cwd, 'src', 'AppPlugins', 'P4Houdini'))
        # Houdini is only happy with /
        src_env = 'HOUDINI_PATH = %s;&' % (hou_plugin_src.replace('\\', '/'))
        
        for userpref in userprefs:
            self.appendToFile(src_env, os.path.join(userpref, 'houdini.env'))

        # hou_pythonrc_py_src = os.path.join(hou_plugin_src, 'python2.7libs', 'pythonrc.py')

        # hou_plugin_dst = os.path.join(userprefs, 'scripts', 'python', 'P4Houdini')
        # hou_pythonrc_py_dst = os.path.join(userprefs, 'scripts', 'python', 'pythonrc.py')

        # if not os.path.exists(hou_plugin_dst):
        #     os.makedirs(hou_plugin_dst)

        # self.install_p4python(hou_plugin_dst)
        # self.install_perforce_module(hou_plugin_dst)

        # logSymlink(hou_pythonrc_py_src, hou_pythonrc_py_dst)




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


def setup():
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
            print "Warning: This prompt isn't elevated (admin), not possible to symlink files. Do a simple copy instead? [Y/N]"
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

def install():
    apps = [ 
                Maya(),
                Nuke(),
                # Katana(), #This is broken atm
                Houdini()
            ]
    for app in apps:
        msg = '-'*25 + ' Setting up Perforce for %s' % (type(app).__name__) + '-'*25
        print '-' * len(msg)
        print msg
        print '-' * len(msg)
        app.install()
        print ''


if __name__ == '__main__':
    setup()
    install()

    print 'Done!'
