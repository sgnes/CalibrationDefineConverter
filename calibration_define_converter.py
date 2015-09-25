__author__ = 'DZMP8F'

import os
import sys
import re

class CaldFileConverter(object):
    def __init__(self, filename):
        self.str_cfile_name = filename
        self.str_cfile_base_name = os.path.splitext(self.str_cfile_name)[0]
        self.str_hfile_name = self.str_cfile_base_name + ".h"
        self.__str_cal_fixed = "Cald_Data_Pflash"
        self.str_modul_name = self.str_cfile_name[:4].upper()
        self.str_struct_name = "Ts{}_CaldData".format(self.str_modul_name)
        self.str_cal_struct_name = "Ks{}_{}".format(self.str_modul_name, self.__str_cal_fixed)
        self.str_cal_pstruct_name = "Kp{}_{}".format(self.str_modul_name, self.__str_cal_fixed)
        self.str_cfile_text_sub = ""
        self.__reexp_cal_def = r"^\s*const\s+([A-Za-z0-9_]{2,40})\s+([A-Za-z0-9_]"\
                                                r"{2,40})\s+([A-Za-z0-9_]{2,40})\s*=\s*([A-Za-z0-9_().\s\n{},-]"\
                                                r"{2,1000});"
        #/\*\s*\n\*\|\s*eosmcald.{\s*\n\*\|\s*([a-zA-Z0-9_]{2,80})\s*{\s*\n(.*?)\s*\*\|\s*}
        self.__reexp_cal_des = r"/\*\s*\n\*\|\s*"+ r"{}".format(self.str_cfile_base_name)\
                               + "\..?{.?\*\|\s*([a-zA-Z0-9_]{2,80})\s*.?{(.*?)\*\|\s*}"
        self.__reexp_cal_des_sub = r"/\*\s*\n\*\|\s*" +  r"{}".format(self.str_cfile_base_name) + r"\..?{.?\*\|\s*([a-zA-Z0-9_]{2,80})" \
                                   r"\s*.?{(.*?)\*\|\s*.*?\*\|\s*}.*?\*\/"
        self.__reexp_cal_c_inlcude = r"/\*+[\s\r\n*]{0,100}Calibration\s+decalaration.*?/"
        self.__reexp_cal_h_del_sub = r"\s*extern\s+const\s+([A-Za-z0-9_]{2,40})\s+([A-Za-z0-9_]{2,40})\s+([A-Za-z0-9_]{2,40})\s*;"
        self.dict_cal_def = {}
        self.dict_cal_des = {}

    def get_calibration_info(self):
        if self.str_cfile_name.endswith("cald.c") and os.path.exists(self.str_hfile_name):
            self.file_cfile_cald = open(self.str_cfile_name)
            if self.file_cfile_cald:
                self.str_cfile_text = self.file_cfile_cald.read()
                self.list_mat_cfile_cald = re.findall(self.__reexp_cal_def,self.str_cfile_text, re.M)

                for i in self.list_mat_cfile_cald:
                    self.dict_cal_def[i[2]] = i
                self.list_mat_cfile_cald_des = re.findall(self.__reexp_cal_des,self.str_cfile_text, re.S)
                for i in self.list_mat_cfile_cald_des:
                    self.dict_cal_des[i[0]] = i[1]
            self.file_cfile_cald.close()
        else:
            self.dict_cal_def = []
        return self.dict_cal_def

    def generate_new_cal_def(self):
        self.str_cal_c_define = "const {} {} = {}\r\n".format(self.str_struct_name, self.str_cal_struct_name, "{")
        self.str_cal_c_des = "/*\n*| {}.{}\n*|   {} {}\n*|     : is_calconst;".\
                        format(self.str_cfile_base_name,"{", self.str_cal_struct_name,"{")
        for i in self.dict_cal_def:
            self.str_cal_c_define += "{},\r\n".format(self.dict_cal_def[i][3])
            self.str_cal_c_des += "\n*|     .__{0} {1}{2}*|     {3}".format(i, "{",
                                                                          self.dict_cal_des[i].
                                                                          replace("*|", "*|     "), "}")
        self.str_cal_c_define = self.str_cal_c_define[:len(self.str_cal_c_define)-3] + "\r\n};\r\n"
        self.str_cal_c_define += "const {} * const {} = &{};\r\n".\
                                                                format(self.str_struct_name,
                                                                    self.str_cal_pstruct_name, self.str_cal_struct_name)
        self.str_cal_c_des += "\n*|   }\n*| }\r\n*/\n"
        file_cfile_cald = open(self.str_cfile_name + ".i", "w")
        if file_cfile_cald:
            file_cfile_cald.write(self.str_cal_c_des)
            file_cfile_cald.write(self.str_cal_c_define)
        file_cfile_cald.close()

        return  self.str_cal_c_des + self.str_cal_c_define

    def generate_new_cal_del(self):
        self.str_cal_type_define = "\ntypedef struct {}_t\r\n{}\r\n".format(self.str_struct_name, "{")
        self.str_cal_h_define = ""
        for i in self.dict_cal_def:
            self.str_cal_type_define += "   {}   __{};\r\n".format(self.dict_cal_def[i][0],self.dict_cal_def[i][2])
            self.str_cal_h_define += "#define {} {}->__{}\r\n".format(self.dict_cal_def[i][2], self.str_cal_pstruct_name, self.dict_cal_def[i][2])
        self.str_cal_type_define += "{} {};\r\n".format("}", self.str_struct_name)
        self.str_cal_h_extern = "#pragma section CONST \".calibrationData\"\n"
        self.str_cal_h_extern += "#pragma use_section CONST {}\n".format(self.str_cal_struct_name)
        self.str_cal_h_extern += "extern const {} {};\n".format(self.str_struct_name, self.str_cal_struct_name)
        self.str_cal_h_extern += "#pragma section CONST \".calibrationPointer\"\n"
        self.str_cal_h_extern += "#pragma use_section CONST {}\n".format(self.str_cal_pstruct_name)
        self.str_cal_h_extern += "extern const {} * const {};".format(self.str_struct_name, self.str_cal_pstruct_name)

        file_hfile_cald = open(self.str_hfile_name + ".i","w")
        if file_hfile_cald:
            file_hfile_cald.write(self.str_cal_type_define)
            file_hfile_cald.write(self.str_cal_h_define)
            file_hfile_cald.write(self.str_cal_h_extern)
        file_hfile_cald.close()
        return  self.str_cal_type_define + self.str_cal_h_define + self.str_cal_h_extern

    def update_old_files(self):
        if self.str_cfile_name.endswith("cald.c") and os.path.exists(self.str_hfile_name):
            self.file_cfile_cald = open(self.str_cfile_name, "w")
            if self.file_cfile_cald:
                self.str_cfile_text_sub = re.sub(self.__reexp_cal_des_sub, "", self.str_cfile_text, 99999, re.S)
                self.str_cfile_text_sub = re.sub(self.__reexp_cal_def, self.str_cal_c_des + self.str_cal_c_define, self.str_cfile_text_sub,1,re.M)
                self.str_cfile_text_sub = re.sub(self.__reexp_cal_def, "", self.str_cfile_text_sub,9999,re.M)
                #self.str_cfile_text_sub = re.sub(self.__reexp_cal_c_inlcude, "\r\n#include \"{}\"\r\n".
                #                                 format(self.str_cfile_name + ".i"), self.str_cfile_text_sub, 1, re.S)
                self.file_cfile_cald.write(self.str_cfile_text_sub)
            self.file_cfile_cald.close()
            self.__file_cald_hfile = open(self.str_hfile_name, "r")
            if self.__file_cald_hfile:
                self.str_text_hfile = self.__file_cald_hfile.read()
                self.__file_cald_hfile.close()
                self.__file_cald_hfile = open(self.str_hfile_name, "w")
                self.str_hfile_text_sub = re.sub(self.__reexp_cal_h_del_sub, self.str_cal_type_define + self.str_cal_h_define + self.str_cal_h_extern, self.str_text_hfile, 1)
                self.str_hfile_text_sub = re.sub(self.__reexp_cal_h_del_sub, "", self.str_hfile_text_sub, 9999)
                self.__file_cald_hfile.write(self.str_hfile_text_sub)
                pass
            self.__file_cald_hfile.close()
#const T_RPMa              CAL0ADDR KfENGN_n_HiRPM_Calc_ThrshLo    = V_RPMa(5500);
def main():
    _str_cal_fixed = "Cald_Data_Pflash"
    if len(sys.argv) == 2:
        str_cfile_name = sys.argv[1]
        str_modul_name = str_cfile_name[:4].upper()
        str_cfile_base_name = os.path.splitext(str_cfile_name)[0]
        str_cfile_type = os.path.splitext(str_cfile_name)[1]
        str_hfile_name = str_cfile_base_name + ".h"
        str_struct_name = "Ts{}_CaldData".format(str_modul_name)
        str_cal_struct_name = "Ks{}_{}".format(str_modul_name, _str_cal_fixed)
        str_cal_pstruct_name = "Kp{}_{}".format(str_modul_name, _str_cal_fixed)
        str_cal_type_define = ""
        str_cal_h_extern = ""
        str_cal_h_define = ""
        str_cal_c_define = "const {} {} = {}\r\n".format(str_struct_name, str_cal_struct_name, "{")
        str_cal_c_des = "/*\r\n*| {}.{}\r\n*|   {} {}\r\n*|     : is_calconst;\r\n".\
                        format(str_cfile_base_name,"{", str_cal_struct_name,"{")
        dict_cal_des = {}
        if str_cfile_base_name.endswith("cald") and str_cfile_type.__eq__(".c") and os.path.exists(str_hfile_name):
            file_cfile_cald = open(str_cfile_name,"r")
            if file_cfile_cald:
                str_cfile_text = file_cfile_cald.read()
                match_obj_cald_str = re.findall(r"^\s*const\s+([A-Za-z0-9_]{2,40})\s+([A-Za-z0-9_]"
                                                r"{2,40})\s+([A-Za-z0-9_]{2,40})\s+=\s+([A-Za-z0-9_().]"
                                                r"{2,60});",str_cfile_text, re.M)
                list_match_des = re.findall(r"/\*.?\*\|\s*engncald\..?{.?\*\|\s*([a-zA-Z0-9_]{2,80})\s*.?{(.*?)\*\|\s*}",
                                            str_cfile_text, re.S)
                str_cile_without_cal = re.sub(r"const\s+([A-Za-z0-9_]{2,40})\s+([A-Za-z0-9_]"
                                                r"{2,40})\s+([A-Za-z0-9_]{2,40})\s+=\s+([A-Za-z0-9_().]"
                                                r"{2,60});","", str_cfile_text)
                str_cile_without_cal_des = re.sub(r"/\*.?\*\|\s*engncald\..?{.?\*\|\s*([a-zA-Z0-9_]{2,80})\s*.?{(.*?)\*\|\s*.*?\*\|\s*}.*?\*\/",
                                                   "", str_cile_without_cal,99999, re.S)
                if list_match_des:
                    for i in list_match_des:
                        dict_cal_des[i[0]] = i[1]
                if match_obj_cald_str:
                    #print(_str_separator_fixed)
                    str_cal_type_define += "typedef struct {}_t\r\n{}\r\n".format(str_struct_name, "{")
                    for i in match_obj_cald_str:
                        str_cal_type_define += "   {}   __{};\r\n".format(i[0],i[2])
                        str_cal_h_define += "#define {} {}->__{}\r\n".format(i[2], str_cal_pstruct_name, i[2])
                        str_cal_c_define += "{},\r\n".format(i[3])
                        str_cal_c_des += "*|     .__{} {}{}*|     {}\r\n".format(i[2],"{", dict_cal_des[i[2]].replace("*| ", "*|     "),"}")
                    str_cal_type_define += "{} {};\r\n".format("}", str_struct_name)
                    str_cal_c_define = str_cal_c_define[:len(str_cal_c_define)-3] + "\r\n};\r\n"
                    str_cal_c_define += "const {} * const {} = &{};\r\n".format(str_struct_name, str_cal_pstruct_name, str_cal_struct_name)
                    str_cal_c_des += "*|   }\r\n*| }\r\n*/\r\n"
                    str_cal_h_extern += "extern const {} {};\r\n".format(str_struct_name, str_cal_struct_name)
                    str_cal_h_extern += "extern const {} * const {};".format(str_struct_name, str_cal_pstruct_name)
                    print (str_cile_without_cal_des)
                file_cfile_cald.close()
                file_cfile_cald = open(str_cfile_name,"w")
                str_tmp = re.sub(r"/\*+[\s\r\n*]{0,100}Calibration\s+decalaration.*?/","\r\n#include \"{}\"\r\n".format(str_cfile_name + ".i"),str_cile_without_cal_des,1, re.S)
                file_cfile_cald.write(str_tmp)
                file_cfile_cald.close()
                file_cfile_cald = open(str_cfile_name + ".i","w")
                if file_cfile_cald:
                    file_cfile_cald.write(str_cal_c_des)
                    file_cfile_cald.write(str_cal_c_define)
                file_cfile_cald.close()
                file_hfile_cald = open(str_hfile_name + ".i","w")
                if file_hfile_cald:
                    file_hfile_cald.write(str_cal_type_define)
                    file_hfile_cald.write(str_cal_h_define)
                    file_hfile_cald.write(str_cal_h_extern)
                file_hfile_cald.close()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        con = CaldFileConverter(sys.argv[1])
        con.get_calibration_info()
        con.generate_new_cal_def()
        con.generate_new_cal_del()
        con.update_old_files()
