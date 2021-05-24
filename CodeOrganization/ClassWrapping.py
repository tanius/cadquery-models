import cadquery as cq
import logging

# A so-far unsuccessful experiment of how custom parts could be wrapped into classes. A better 
# technique is shown in Case.py in the same directory.

class TestPart(cq.Workplane):

    def __init__(self, param, name = "TestPart", color = None, alpha = None):
        self.param = float(param)
        self.name = name
        self.color = color
        self.alpha = alpha
        
        self.log = logging.getLogger(__name__)
        
        super(TestPart, self).__init__('XY')
        
        self.log.info("DEBUG: __init__(self, param)")


    def build(self):
        self.log.info("DEBUG: build(self)")
        
        # Since CadQuery Workplane methods generally return a copy instead of modifying self, 
        # we cannot do "self.box(100, 100, 100); return self;".
        box = self.box(100, 100, 100)
        return self.union(box)


    def show(self):
        """
        It is somehow not possible to use show_object() with custom classes. To work around that without having to expose 
        an inner CadQuery object, we implement our own show() method for that inner object.
        """
        
        options = {}
        if self.color != None: options["color"] = self.color
        if self.alpha != None: options["alpha"] = float(self.alpha) # Allow accidental string arguments, unlike show_object().
        
        show_object(self.build(), self.name, options)


part = TestPart(param = 10, name = "my_test_part", color = "blue", alpha = 0.5)
part.show()
