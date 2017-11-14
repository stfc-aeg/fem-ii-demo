import json
import datetime
import sys
import msgpack

# Check the python version at runtime. DECODE_BYTES is True when running on python 3.0 - 3.5
DECODE_BYTES = False
if sys.version_info[0] == 3:
    if sys.version_info[1] <= 5:
        DECODE_BYTES = True


class IpcMessageException(Exception):
    def __init__(self, msg, errno=None):
        self.msg = msg
        self.errno = errno

    def __str__(self):
        return str(self.msg)


class IpcMessage(object):

    ACK = "ack"
    NACK = "nack"

    def __init__(self, msg_type=None, msg_val=None, from_str=None, encoding="msgpack"):
        self.attrs = {}
        self.encoding = encoding.upper()

        if from_str is None:
            self.attrs['msg_type'] = msg_type
            self.attrs['msg_val'] = msg_val
            self.attrs['timestamp'] = datetime.datetime.now().isoformat()
            self.attrs['params'] = {}
        else:
            try:
                if self.encoding == "JSON":
                    # Manually decode bytes when operating in python versions 3.0 - 3.5 inclusive
                    if DECODE_BYTES:
                        from_str = from_str.decode("utf-8")
                    self.attrs = json.loads(from_str)
                elif self.encoding == "MSGPACK":
                        # MsgPack does not decode raw strings back into strings.
                    self.attrs = msgpack.unpackb(from_str, encoding="utf8")
                else:
                    encode_error = "Encoding format %s not recognised or supported" % self.encoding
                    raise IpcMessageException(encode_error)
            except ValueError as e:
                raise IpcMessageException(
                    "Illegal message %s format: " + str(e)) % self.encoding

    def is_valid(self):
        is_valid = True
        try:
            is_valid = is_valid & (self._get_attr("msg_type") is not None)
            is_valid = is_valid & (self._get_attr("msg_val") is not None)
            is_valid = is_valid & (self._get_attr("timestamp") is not None)
        except IpcMessageException:
            is_valid = False

        return is_valid

    def get_msg_type(self):
        return self.attrs['msg_type']

    def get_msg_val(self):
        return self.attrs['msg_val']

    def get_msg_timestamp(self):
        return self.attrs['timestamp']

    def get_param(self, param_name, default_value=None):
        try:
            param_value = self.attrs['params'][param_name]
        except KeyError:
            if default_value is None:
                raise IpcMessageException("Missing parameter " + param_name)
            else:
                param_value = default_value

        return param_value

    def set_msg_type(self, msg_type):
        self.attrs['msg_type'] = msg_type

    def set_msg_val(self, msg_val):
        self.attrs['msg_val'] = msg_val

    def set_param(self, param_name, param_value):
        if "params" not in self.attrs:
            self.attrs['params'] = {}

        self.attrs['params'][param_name] = param_value

    def encode(self):
        if self.encoding == "JSON":
            return json.dumps(self.attrs)
        elif self.encoding == "MSGPACK":
            return msgpack.packb(self.attrs)
        else:
            encode_error = "Encoding format %s not recognised or supported" % self.encoding
            raise IpcMessageException(encode_error)
            
    def __eq__(self, other):
        return self.attrs == other.attrs

    def __ne__(self, other):
        return self.attrs != other.attrs

    def __str__(self):
        output = " {\n"
        if self.encoding == "JSON":
            return json.dumps(self.attrs,
                            sort_keys=True, indent=4, separators=(',', ': '))
        elif self.encoding == "MSGPACK":
            # Does this work in Py2 ?
            for key, value in sorted(self.attrs.items()):
                try:
                    if isinstance (value, dict):
                        output += "     \"" + str(key) + "\": {\n"
                        for key2, value2 in sorted(value.items()):
                            output += "         \"" + str(key2) + "\": \"" + str(value2) + "\",\n"
                        output += "     },\n"
                    else:
                        output += "     \"" + str(key) + "\": \"" + str(value) + "\",\n"
                except TypeError as e:
                    raise IpcMessageException("Couldn't cast to string: " + str(e))
            output+= "}"
            return output
        else:
            raise IpcMessageException("Encoding format %s not recognised or supported") % self.encoding


    def _get_attr(self, attr_name, default_value=None):

        try:
            attr_value = self.attrs[attr_name]
        except KeyError:
            if default_value is None:
                raise IpcMessageException("Missing attribute " + attr_name)
            else:
                attr_value = default_value

        return attr_value
