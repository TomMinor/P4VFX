import os

from P4 import P4, P4Exception

from perforce.Utils import p4Logger

def connect(p4):
    if not p4.connected():
        # By setting P4's CWD to the settings folder, the user can create a 
        # P4CONFIG file per app. If they have already set an absolute path
        # for P4CONFIG, then this will have no effect.
        # Otherwise P4 will search upwards until it finds a p4config file
        from perforce.AppInterop import interop
        p4.cwd = interop.getSettingsPath()

        p4Logger().info('Connecting to server... %s' % p4.port)
        p4Logger().debug('Using p4config file: %s' % p4.p4config_file)
        p4.connect()

    try:
        root = p4.fetch_client()
    except P4Exception as e:
        p4Logger().info('Attempting to login...')
        try:
            from perforce.GUI import LoginWindow
            LoginWindow.setP4Password(p4)
        except P4Exception as e:
            p4Logger().warning('Couldn\'t login to server')
            p4.disconnect()
            raise

        try:
            root = p4.fetch_client()
        except P4Exception as e:
            raise e

        p4Logger().info('Connected to server! [%s]' % (root))

    try:
        tmp = p4.run_info()
        info = tmp[0]
    except P4Exception as e:
        p4Logger().error( e.msg )
        raise e

    if info['clientName'] == '*unknown*':
        msg = 'Perforce client is unknown, please edit your P4CONFIG file and specify a value for P4CLIENT or use "p4 set"'
        p4Logger().debug(p4.cwd)
        p4Logger().debug('P4CONFIG=%s'%os.environ.get('P4CONFIG'))
        p4Logger().error(msg)
        raise ValueError(msg)

    # By default the cwd will be the same as the host's executable location,
    # so change it to the workspace root
    try:
        p4.cwd = info['clientRoot'] 
        p4Logger().debug('Setting P4 cwd to %s', p4.cwd)
    except P4Exception as e:
        p4Logger().error(e.msg)
        raise e    

    # for key in info:
    #     p4Logger().debug( '\t%s:\t%s' % (key, info[key]) )

    p4Logger().debug("Perforce CWD: %s" % p4.cwd)
