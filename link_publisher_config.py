import datetime


# |nid| means Naver ID.
def create_link_publish_config_filepath(nid):
    link_publisher_config_filepath = f'%s.config' % (nid)
    return link_publisher_config_filepath


def read_link_publisher_config(nid):
    return read_link_publisher_config_from_file(nid)


def read_link_publisher_config_from_file(nid):
    filepath = create_link_publish_config_filepath(nid)
    try:
        f = open(filepath, 'rb')
        config = f.readline().decode('utf-8')
        config = config.strip()
        f.close()
        return config
    except IOError as e:
        return None


def write_link_publisher_config(nid):
    today = datetime.date.today()
    output = f'%04d-%02d-%2d' % (today.year, today.month, today.day)
    write_link_publisher_config_to_file(nid, output)


def write_link_publisher_config_to_file(nid, output):
    filepath = create_link_publish_config_filepath(nid)
    try:
        f = open(filepath, 'wb')
        f.write(output.encode('utf-8'))
        ln = '\n'
        f.write(ln.encode('utf-8'))
        f.close()
    except IOError as e:
        print('[ERROR] An IOError has been occurred.')
        print(e)


def test_all():
    nid = 'foobar'
    read_link_publisher_config_from_file(nid)
    write_link_publisher_config(nid)


if __name__ == '__main__':
    test_all()
