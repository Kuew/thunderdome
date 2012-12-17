from unittest import skip
from thunderdome.tests.base import BaseCassEngTestCase

from thunderdome.models import Vertex, Edge
from thunderdome import columns

class TestModel(Vertex):
    count   = columns.Integer()
    text    = columns.Text(required=False)
    
class TestEdge(Edge):
    numbers = columns.Integer()

class TestEdgeIO(BaseCassEngTestCase):

    def setUp(self):
        super(TestEdgeIO, self).setUp()
        self.v1 = TestModel.create(count=8, text='a')
        self.v2 = TestModel.create(count=7, text='b')
        
    def test_model_save_and_load(self):
        """
        Tests that models can be saved and retrieved
        """
        e1 = TestEdge.create(self.v1, self.v2, numbers=3)
        
        edges = self.v1.outE()
        assert len(edges) == 1
        assert edges[0].eid == e1.eid
        
    def test_model_updating_works_properly(self):
        """
        Tests that subsequent saves after initial model creation work
        """
        e1 = TestEdge.create(self.v1, self.v2, numbers=3)

        e1.numbers = 20
        e1.save()
        
        edges = self.v1.outE()
        assert len(edges) == 1
        assert edges[0].numbers == 20

    def test_model_deleting_works_properly(self):
        """
        Tests that an instance's delete method deletes the instance
        """
        e1 = TestEdge.create(self.v1, self.v2, numbers=3)
        
        e1.delete()
        edges = self.v1.outE()
        assert len(edges) == 0
            
