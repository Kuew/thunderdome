from thunderdome.tests.base import BaseCassEngTestCase

from thunderdome.exceptions import ModelException
from thunderdome.models import Vertex, Edge
from thunderdome import columns
import thunderdome

from thunderdome.tests.base import TestModel

class WildDBNames(Vertex):
    content = columns.Text(db_field='words_and_whatnot')
    numbers = columns.Integer(db_field='integers_etc')
            
class Stuff(Vertex):
    num = columns.Integer()

class TestModelClassFunction(BaseCassEngTestCase):
    """
    Tests verifying the behavior of the Model metaclass
    """

    def test_column_attributes_handled_correctly(self):
        """
        Tests that column attributes are moved to a _columns dict
        and replaced with simple value attributes
        """

        #check class attibutes
        self.assertHasAttr(TestModel, '_columns')
        self.assertHasAttr(TestModel, 'vid')
        self.assertHasAttr(TestModel, 'text')

        #check instance attributes
        inst = TestModel()
        self.assertHasAttr(inst, 'vid')
        self.assertHasAttr(inst, 'text')
        self.assertIsNone(inst.vid)
        self.assertIsNone(inst.text)

    def test_db_map(self):
        """
        Tests that the db_map is properly defined
        -the db_map allows columns
        """


        db_map = WildDBNames._db_map
        self.assertEquals(db_map['words_and_whatnot'], 'content')
        self.assertEquals(db_map['integers_etc'], 'numbers')

    def test_attempting_to_make_duplicate_column_names_fails(self):
        """
        Tests that trying to create conflicting db column names will fail
        """

        with self.assertRaises(ModelException):
            class BadNames(Vertex):
                words = columns.Text()
                content = columns.Text(db_field='words')

    def test_value_managers_are_keeping_model_instances_isolated(self):
        """
        Tests that instance value managers are isolated from other instances
        """
        inst1 = TestModel(count=5)
        inst2 = TestModel(count=7)

        self.assertNotEquals(inst1.count, inst2.count)
        self.assertEquals(inst1.count, 5)
        self.assertEquals(inst2.count, 7)

class RenamedTest(thunderdome.Vertex):
    element_type = 'manual_name'
    
    id = thunderdome.UUID(primary_key=True)
    data = thunderdome.Text()
        
class TestManualTableNaming(BaseCassEngTestCase):
    
    def test_proper_table_naming(self):
        assert RenamedTest.get_element_type() == 'manual_name'











