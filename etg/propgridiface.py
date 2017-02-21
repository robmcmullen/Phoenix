#---------------------------------------------------------------------------
# Name:        etg/propgridiface.py
# Author:      Robin Dunn
#
# Created:     23-Feb-2015
# Copyright:   (c) 2015-2017 by Total Control Software
# License:     wxWindows License
#---------------------------------------------------------------------------

import etgtools
import etgtools.tweaker_tools as tools

PACKAGE   = "wx"
MODULE    = "_propgrid"
NAME      = "propgridiface"   # Base name of the file to generate to for this script
DOCSTRING = ""

# The classes and/or the basename of the Doxygen XML files to be processed by
# this script.
ITEMS  = [ 'wxPGPropArgCls',
           'wxPropertyGridInterface',
           ]

#---------------------------------------------------------------------------

def run():
    # Parse the XML file(s) building a collection of Extractor objects
    module = etgtools.ModuleDef(PACKAGE, MODULE, NAME, DOCSTRING)
    etgtools.parseDoxyXML(module, ITEMS)

    #-----------------------------------------------------------------
    # Tweak the parsed meta objects in the module object as needed for
    # customizing the generated code and docstrings.

    c = module.find('wxPGPropArgCls')
    assert isinstance(c, etgtools.ClassDef)
    c.find('wxPGPropArgCls').findOverload('deallocPtr').ignore()
    c.find('GetPtr').overloads[0].ignore()
    c.convertFromPyObject = """\
        // Code to test a PyObject for compatibility with wxPGPropArgCls
        if (!sipIsErr) {
            if (PyBytes_Check(sipPy) || PyUnicode_Check(sipPy))
                return TRUE;
            if (sipCanConvertToType(sipPy, sipType_wxPGProperty, SIP_NO_CONVERTORS))
                return TRUE;
            return FALSE;
        }

        // Code to convert a compatible PyObject to a wxPGPropArgCls
        if (PyBytes_Check(sipPy) || PyUnicode_Check(sipPy)) {
            *sipCppPtr = new wxPGPropArgCls(Py2wxString(sipPy));
            return sipGetState(sipTransferObj);
        }
        else {
            wxPGProperty* prop = reinterpret_cast<wxPGProperty*>(
                sipConvertToType(sipPy, sipType_wxPGProperty, sipTransferObj, SIP_NO_CONVERTORS, 0, sipIsErr));
            *sipCppPtr = new wxPGPropArgCls(prop);
            return sipGetState(sipTransferObj);
        }
        """


    c = module.find('wxPropertyGridInterface')
    c.abstract = True
    for m in c.findAll('GetIterator'):
        if m.type == 'wxPropertyGridConstIterator':
            m.ignore()

    c.find('SetPropertyValue').findOverload('int value').ignore()
    c.find('SetPropertyValue').findOverload('bool value').ignore()
    c.find('SetPropertyValue').findOverload('wxLongLong_t value').ignore()
    c.find('SetPropertyValue').findOverload('wxULongLong_t value').ignore()
    c.find('SetPropertyValue').findOverload('wxObject *value').ignore()

    c.find('Append.property').transfer = True
    c.find('AppendIn.newProperty').transfer = True
    for m in c.find('Insert').all():
        m.find('newProperty').transfer = True


    c.addPyMethod('RegisterEditor', '(self, editor, editorName=None)',
        body="""\
            if not isinstance(editor, PGEditor):
                editor = editor()
            if not editorName:
                editorName = editor.__class__.__name__
            try:
                self._editor_instances.append(editor)
            except:
                self._editor_instances = [editor]
            return PropertyGrid.DoRegisterEditorClass(editor, editorName)
            """
        )

    module.addItem(
        tools.wxArrayPtrWrapperTemplate('wxArrayPGProperty', 'wxPGProperty', module))


    # wxPGPropArg is a typedef for "const wxPGPropArgCls&" so having the
    # wrappers treat it as a normal type can be problematic. ("new cannot be
    # applied to a reference type", etc.) Let's just ignore it an replace it
    # everywhere for the real type.
    module.find('wxPGPropArg').ignore()
    for item in module.allItems():
        if hasattr(item, 'type') and item.type == 'wxPGPropArg':
            item.type = 'const wxPGPropArgCls &'


    #-----------------------------------------------------------------
    tools.doCommonTweaks(module)
    tools.runGenerators(module)


#---------------------------------------------------------------------------
if __name__ == '__main__':
    run()

