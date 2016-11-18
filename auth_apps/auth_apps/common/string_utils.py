#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re

__author__ = "konglh <psauxq@gmail.com>"
__date__ = "2014-12-18"


def has_chinese(content):
    """判断字符串是否有中文"""
    iconv_content = unicode(content)
    cn_char_pattern = re.compile(u'[\u4e00-\u9fa5]+')
    match = cn_char_pattern.search(iconv_content)
    return True if match else False


def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    return uchar >= u'\u4e00' and uchar <= u'\u9fa5'


def is_number(uchar):
    """判断一个unicode是否是数字"""
    return uchar >= u'\u0030' and uchar <= u'\u0039'


def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    return (uchar >= u'\u0041' and uchar <= u'\u005a') or (uchar >= u'\u0061' and uchar <= u'\u007a')


def is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    return not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar))


def half2full(uchar):
    """半角转全角"""
    inside_code = ord(uchar)
    if inside_code < 0x0020 or inside_code > 0x7e:
        # 不是半角字符就返回原来的字符
        return uchar

    if inside_code == 0x0020:
        # 除了空格其他的全角半角的公式为:半角=全角-0xfee0
        inside_code = 0x3000
    else:
        inside_code += 0xfee0

    return unichr(inside_code)


def full2half(uchar):
    """全角转半角"""
    inside_code = ord(uchar)

    if inside_code == 0x3000:
        inside_code = 0x0020
    else:
        inside_code -= 0xfee0

    if inside_code < 0x0020 or inside_code > 0x7e:
        # 转完之后不是半角字符返回原来的字符
        return uchar

    return unichr(inside_code)


def str_half2full(ustring):
    """把字符串半角转全角"""
    return "".join([half2full(uchar) for uchar in ustring])


def str_full2half(ustring):
    """把字符串全角转半角"""
    return "".join([full2half(uchar) for uchar in ustring])


def utf8str_half2full(utf8string):
    """把字符串半角转全角"""
    ustring = utf8string.decode('utf-8')
    return "".join([half2full(uchar) for uchar in ustring]).encode('utf-8')


def utf8str_full2half(utf8string):
    """把字符串全角转半角"""
    ustring = utf8string.decode('utf-8')
    return "".join([full2half(uchar) for uchar in ustring]).encode('utf-8')


def uniform(ustring):
    """格式化字符串，完成全角转半角，大写转小写的工作"""
    return str_full2half(ustring).lower()


if __name__ == "__main__":
    # test full2half and half2full
    for i in range(0x0020, 0x007F):
        print full2half(half2full(unichr(i))), half2full(unichr(i))

    # test uniform
    ustring = u'中国 人名ａ高频Ａ'
    ustring = uniform(ustring)

    print ustring
