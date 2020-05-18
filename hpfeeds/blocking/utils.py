def get_inet_version(host):
    """ Returns AF_NET or AF_INET6 depending on support"""
    try:
        if hasattr(socket, 'AF_INET6') and socket.getaddrinfo(host, None, socket.AF_INET6):
            return socket.AF_INET6
    except Exception as e:
        logging.exception(e)
            
    return socket.AF_INET
