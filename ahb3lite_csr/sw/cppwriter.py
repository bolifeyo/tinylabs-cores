#!/usr/bin/env python
#
# cppwriter takes a list of fields and generates a cpp header to
# assist in accessing generated CSRs
#
# All rights reserved
# Tiny Labs Inc
# 2020
#

from ahb3lite_csr import Field, Reg

#class FieldIter:
#    def __init__(self):
#        self.
class CPPWriter:
    def __init__(self, name, field):
        self.name = name
        self.field = field

    def header (self, cid):
        s =  '// This file is autogenerated by csrgen - DO NOT EDIT\n'
        s += '#ifndef ' + cid + '\n'
        s += '#define ' + cid + '\n'
        s += '#include <stdint.h>\n\n'
        s += 'typedef struct {\n'
        s += '\tuint32_t off;\n\tuint32_t sht;\n'
        s += '} ' + self.name + '_t;\n\n'
        return s

    def footer (self, cid):
        s = '#endif /* ' + cid + ' */\n'
        return s
    
    def write(self, filename):
        cid = filename.replace ('.', '_').upper ()

        #print ("Writing cpp header: " + filename)
        with open (filename, 'w') as fh:
            
            # Write header
            fh.write (self.header (cid))

            # Create host interface
            s = '#ifdef HOST_INTERFACE\n\n'

            # Create field defs
            for f in self.field:
                if f.count == 1:
                    s += '#define ' + f.offset() + '\t' + str(f.rptr[0].reg.address) + '\n'
                    s += '#define ' + f.shift() + '\t' + str(f.rptr[0].offset) + '\n'
                    s += '#define ' + f.mask() + '\t' + hex(2 ** f.width - 1) + '\n'
                else:
                    s += 'static ' + self.name + '_t ' + f.name + '_n[' + str(f.count) + '] = {\n'
                    for n in range (f.count):
                        s += '\t{' + str(f.rptr[n].reg.address) + ', ' + str(f.rptr[n].offset) + '},\n'
                    s += '};\n'
                    s += '#define ' + f.mask() + '\t' + hex(2 ** f.width - 1) + '\n'
                    s += '#define ' + f.maximum() + '\t' + str(f.count) + '\n'
                    
            # Create class
            s += '\nclass ' + self.name + ' {\n'
            s += '  private:\n'
            s += '\tuint32_t (*read)(uint32_t);\n'
            s += '\tvoid (*write)(uint32_t, uint32_t);\n'
            s += '\tuint32_t base;\n'
            s += '  public:\n'
            s += '\t' + self.name + ' (uint32_t base, uint32_t (*read)(uint32_t), void (*write)(uint32_t, uint32_t)) {\n'
            s += '\t\tthis->read = read;\n'
            s += '\t\tthis->write = write;\n'
            s += '\t\tthis->base = base;\n'
            s += '\t}\n'

            # Generate field accessors
            for f in self.field:
                # Read accessor
                if f.rtype != 'wo':
                    if f.count == 1:
                        s += '\tuint32_t ' + f.name + ' (void) {\n'
                        s += '\t\treturn (read (base + ' + f.offset() + ') '
                        s += '>> ' + f.shift() + ') & ' + f.mask() + ';\n'
                        s += '\t}\n'
                    else:
                        s += '\tuint32_t ' + f.name + ' (uint32_t idx) {\n'
                        s += '\t\tif (idx >= ' + f.maximum() + ') return 0;\n'
                        s += '\t\treturn (read (base + ' + f.name + '_n[idx].off) '
                        s += '>> ' + f.name + '_n[idx].sht) & ' + f.mask() + ';\n'
                        s += '\t}\n'
                        
                # Write accesor ie: read/modify/write
                if f.rtype != 'ro':
                    if f.count == 1:
                        s += '\tvoid ' + f.name + ' (uint32_t val) {\n'
                        # Read
                        s += '\t\tuint32_t p = read (base + ' + f.offset() + ');\n'
                        # Modify
                        s += '\t\tp &= ~(' + f.mask() + ' << ' + f.shift() + ');\n'
                        s += '\t\tp |= ((val & ' + f.mask() + ') << ' + f.shift() + ');\n'
                        # Write
                        s += '\t\twrite (base + ' + f.offset() + ', p);\n'
                        s += '\t}\n'
                    else:
                        s += '\tvoid ' + f.name + ' (uint32_t idx, uint32_t val) {\n'
                        s += '\t\tif (idx >= ' + f.maximum() + ') return;\n'
                        # Read
                        s += '\t\tuint32_t p = read (base + ' + f.name + '_n[idx].off);\n'
                        # Modify
                        s += '\t\tp &= ~(' + f.mask() + ' << ' + f.name + '_n[idx].sht);\n'
                        s += '\t\tp |= ((val & ' + f.mask() + ') << ' + f.name + '_n[idx].sht);\n'
                        # Write
                        s += '\t\twrite (base + ' + f.name + '_n[idx].off, p);\n'
                        s += '\t}\n'
                        
                    
            # Close class
            s += '};\n\n'
            s += '#else /* !HOST_INTERFACE */\n\n'
            fh.write (s)

            # Create target interface
            s = 'typedef struct {\n'
            reg = None
            pwidth = 32
            for f in self.field:
                if f.rptr[0].reg is not reg:
                    if pwidth != 32:
                        s += '\tuint32_t :0;\n'
                    reg = f.rptr[0].reg
                pwidth = f.width
                if f.count == 1:
                    s += '\t/* ' + f.rtype + ' */ volatile uint32_t ' + f.name
                else:
                    s += '\t/* ' + f.rtype + ' */ volatile uint32_t ' + f.name + '[' + str(f.count) + ']'
                if f.width != 32:
                    s += ' : ' + str(f.width) + ';\n'
                else:
                    s += ';\n'
            s +=  '} ' + self.name + ';\n\n'
            s += '#endif /* !HOST_INTERFACE */\n'
            fh.write (s)

            # Write footer
            fh.write (self.footer (cid))
            
