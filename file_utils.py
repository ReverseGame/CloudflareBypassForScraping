
import os
import shutil
import sys
import time
import zipfile

# Chrome代理模板插件(https://github.com/RobinDev/Selenium-Chrome-HTTP-Private-Proxy)目录
PROXY_HELPER = 'Chrome-proxy-helper'
# 存储自定义Chrome代理扩展文件的目录
CUSTOM_CHROME_PROXY_EXTENSIONS_DIR = 'chrome-proxy-extensions'


def generate_proxy_extension(proxy, user_data_dir):
    """获取一个Chrome代理扩展,里面配置有指定的代理(带用户名密码认证)
    proxy - 指定的代理,格式: username:password@ip:port
    """
    new_proxy = proxy.replace('http://', '').replace('https://', '')
    # extension_file_path = generate_extension_zip(new_proxy)  # 生成插件的zip文件
    extension_file_path = generate_extension_dir(new_proxy, user_data_dir)  # 生成插件的目录
    return extension_file_path


# 生成插件的zip文件
def generate_extension_dir(proxy, user_data_dir):
    ip, port, username, password = format_proxy(proxy)
    print(ip, port, username, password)
    # 创建一个定制Chrome代理扩展
    custom_chrome_proxy_extensions_dir = os.path.join(os.getcwd(), user_data_dir)
    extension_file_path = os.path.join(custom_chrome_proxy_extensions_dir, proxy.replace(':', '_'))
    os.makedirs(extension_file_path, exist_ok=True)

    # chrome_proxy_helper_dir = os.path.join(os.getcwd(), PROXY_HELPER)
    chrome_proxy_helper_dir = get_resource_path(PROXY_HELPER)
    os.makedirs(chrome_proxy_helper_dir, exist_ok=True)

    source_manifest = os.path.join(chrome_proxy_helper_dir, 'manifest.json')
    shutil.copy(source_manifest, extension_file_path)

    # 替换模板中的代理参数
    background_content = open(os.path.join(chrome_proxy_helper_dir, 'background.js')).read()
    background_content = background_content.replace('%proxy_host', ip)
    background_content = background_content.replace('%proxy_port', port)
    background_content = background_content.replace('%username', username)
    background_content = background_content.replace('%password', password)
    with open(os.path.join(extension_file_path, 'background.js'), 'w') as f:
        f.write(background_content)

    return extension_file_path


# 生成插件的zip文件
def generate_extension_zip(proxy):
    ip, port, username, password = format_proxy(proxy)
    print(ip, port, username, password)
    # 创建一个定制Chrome代理扩展(zip文件)
    if not os.path.exists(CUSTOM_CHROME_PROXY_EXTENSIONS_DIR):
        os.mkdir(CUSTOM_CHROME_PROXY_EXTENSIONS_DIR)
    extension_file_path = os.path.join(CUSTOM_CHROME_PROXY_EXTENSIONS_DIR, '{}.zip'.format(proxy.replace(':', '_')))
    if not os.path.exists(extension_file_path):
        chrome_proxy_helper_dir = os.path.join(os.getcwd(), PROXY_HELPER)
        # 扩展文件不存在，创建
        zf = zipfile.ZipFile(extension_file_path, mode='w')
        if not os.path.exists(chrome_proxy_helper_dir):
            os.mkdir(chrome_proxy_helper_dir)
        zf.write(os.path.join(chrome_proxy_helper_dir, 'manifest.json'), 'manifest.json')

        # 替换模板中的代理参数
        background_content = open(os.path.join(chrome_proxy_helper_dir, 'background.js')).read()
        background_content = background_content.replace('%proxy_host', ip)
        background_content = background_content.replace('%proxy_port', port)
        background_content = background_content.replace('%username', username)
        background_content = background_content.replace('%password', password)
        zf.writestr('background.js', background_content)
        zf.close()
    return extension_file_path


def get_resource_path(relative_path):
    """获取打包后资源文件的路径"""
    # 打包后使用 sys._MEIPASS，未打包时使用当前目录
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def format_proxy(proxy):
    new_proxy = proxy.replace('http://', '').replace('https://', '')
    if '@' in new_proxy:
        arr = new_proxy.split('@')
        new_proxy = f'{arr[1]}:{arr[0]}'

    split_arr = new_proxy.split(':')
    if len(split_arr) != 4:
        raise Exception('Invalid proxy format. Should be username:password@ip:port')
    ip, port, username, password = split_arr
    return ip, port, username, password


def del_user_data_dir(user_data_dir):
    try:
        custom_chrome_proxy_extensions_dir = os.path.join(os.getcwd(), user_data_dir)
        if os.path.exists(custom_chrome_proxy_extensions_dir):
            shutil.rmtree(custom_chrome_proxy_extensions_dir)
    except PermissionError as e:
        print('')
