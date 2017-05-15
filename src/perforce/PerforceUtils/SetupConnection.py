import os

from P4 import P4, P4Exception

from perforce.Utils import p4Logger

def connect(p4):
    if not p4.connected():
        p4Logger().info('Connecting to server...')
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
        msg = 'Perforce client is unknown, please set the P4CONFIG environment variable to a config file containing your Perforce settings'
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

    for key in info:
        p4Logger().debug( '\t%s:\t%s' % (key, info[key]) )

    p4Logger().debug("Perforce CWD: %s" % p4.cwd)
    # if p4.p4config_file == 'noconfig':
    #     loadP4Config(p4)
