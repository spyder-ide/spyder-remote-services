from jupyterhub.singleuser.mixins import make_singleuser_app

from spyder_remote_server.jupyter_server.serverapp import SpyderServerApp


SingleUserSpyderServerApp = make_singleuser_app(SpyderServerApp)

main = launch_new_instance = SingleUserSpyderServerApp.launch_instance

if __name__ == '__main__':
    main()
