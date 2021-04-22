from py4j.java_gateway import JavaGateway
import py4j

if __name__ == '__main__':

    gw = JavaGateway()
    mm = gw.entry_point
    try:
        mm.logs()  # Just testing for connection
    except py4j.protocol.Py4JNetworkError as e:
        raise e

    plugs = mm.plugins().getMenuPlugins()
    pwsPlug = plugs['edu.bpl.pwsplugin.PWSPlugin']
    assert pwsPlug is not None
    api = pwsPlug.api()

    a = 1