from .reach import ReachAlgorithmPlugin

def classFactory(iface):
    return ReachAlgorithmPlugin(iface)
