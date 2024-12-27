# Base64 编码表
import time

BASE64_ALPHABET = "AYZaOP5bcICijN9p/z0K3FGJBHwLM7ftEo6Q4xy+Xs1Sklmn8TUVghuv2deDRqrW"
BASE64_PADDING = "="

# Base64 解码表
BASE64_REVERSE_ALPHABET = {ord(char): index for index, char in enumerate(BASE64_ALPHABET)}


def base64_encode(input_bytes):
    """
    将字节数组编码为 Base64 字符串
    :param input_bytes: 输入字节数组
    :return: Base64 编码的字符串
    """
    output = []
    i = 0
    len_input = len(input_bytes)

    while i < len_input:
        byte1 = input_bytes[i]
        i += 1
        byte2 = input_bytes[i] if i < len_input else 0
        i += 1
        byte3 = input_bytes[i] if i < len_input else 0
        i += 1

        chunk = [
            byte1 >> 2,
            ((byte1 & 0x03) << 4) | (byte2 >> 4),
            ((byte2 & 0x0f) << 2) | (byte3 >> 6),
            byte3 & 0x3f,
            ]

        if i == len_input + 1:
            chunk.pop(2)
        elif i == len_input + 2:
            chunk.pop(3)

        output.extend(BASE64_ALPHABET[index] for index in chunk)

    # 添加填充字符
    while len(output) % 4 != 0:
        output.append(BASE64_PADDING)

    return ''.join(output)


def base64_decode(input_string):
    """
    将 Base64 字符串解码为字节数组
    :param input_string: Base64 编码的字符串
    :return: 解码后的字节数组
    """
    input_string = input_string.rstrip(BASE64_PADDING)
    output = []
    i = 0
    len_input = len(input_string)

    while i < len_input:
        char1 = BASE64_REVERSE_ALPHABET[ord(input_string[i])]
        i += 1
        char2 = BASE64_REVERSE_ALPHABET[ord(input_string[i])]
        i += 1
        char3 = BASE64_REVERSE_ALPHABET[ord(input_string[i])] if i < len_input else 0
        i += 1
        char4 = BASE64_REVERSE_ALPHABET[ord(input_string[i])] if i < len_input else 0
        i += 1

        byte1 = (char1 << 2) | (char2 >> 4)
        byte2 = ((char2 & 0x0f) << 4) | (char3 >> 2)
        byte3 = ((char3 & 0x03) << 6) | char4

        output.append(byte1)
        if i - 2 < len_input and char3 != 64:
            output.append(byte2)
        if i - 1 < len_input and char4 != 64:
            output.append(byte3)

    return bytes(output)


def base64_decode_to_string(input_string):
    """
    将 Base64 字符串解码为普通字符串
    :param input_string: Base64 编码的字符串
    :return: 解码后的字符串
    """
    decoded_bytes = base64_decode(input_string)
    return decoded_bytes.decode('utf-8')


def check_base64_string(encoded_str, port: str, dif_value: int):
    decoded_str = base64_decode_to_string(encoded_str)
    end_str = f'9{port}'
    if decoded_str and decoded_str.endswith(end_str) and len(decoded_str) - len(port) - 1 == 13:
        cur_mils = int(time.time() * 1000)
        param_mils = int(decoded_str[0:13])
        if abs(cur_mils - param_mils) <= dif_value:
            return True
    return False


# 测试
# if __name__ == "__main__":
#     original_text = "1735290767284912306"
#     # encoded = base64_encode(original_text.encode('utf-8'))
#     # print("Encoded:", encoded.upper())
#
#     decoded = base64_decode_to_string('jKMVNKcdjaMuNVc2Na4TjQj8NE==')
#     print("Decoded:", decoded)
