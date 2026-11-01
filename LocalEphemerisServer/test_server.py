import unittest
from datetime import datetime
from server import chart

class EphemerisTests(unittest.TestCase):
    def test_reference_chart(self):
        result=chart({'utc':'2000-01-01T12:00:00Z','latitude':45.44,'longitude':16.28})
        self.assertEqual(result['ayanamsha'],'Lahiri')
        self.assertEqual(result['nodeType'],'Mean Rahu')
        self.assertGreaterEqual(len(result['planets']),9)
        for body in [result['ascendant'],*result['planets']]:
            self.assertTrue(0<=body['longitude']<360)
            self.assertTrue(1<=body['house']<=12)
            self.assertTrue(1<=body['pada']<=4)
    def test_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            chart({'utc':'2000-01-01T12:00:00Z','latitude':100,'longitude':16.28})

if __name__=='__main__': unittest.main()

class AnnualEndpointTests(unittest.TestCase):
    def test_2025_reference_and_2026_annual(self):
        from server import varshaphala
        request = {'utc':'1985-11-04T00:15:00Z','latitude':45.45,'longitude':16.3667,'year':2025}
        first=varshaphala(request)
        second=varshaphala({**request,'year':2026})
        assert first['annualAscendantSign']=='Vaga'
        assert first['munthaSign']=='Strijelac'
        assert second['annualAscendantSign']=='Jarac'
        assert second['munthaSign']=='Jarac'
        assert len(first['sahams'])==20
        assert first['muddaDasha'][-1]['endUTC']==first['nextSolarReturnUTC']
        assert second['muddaDasha'][-1]['endUTC']==second['nextSolarReturnUTC']
        assert first['varsheshwara']['candidates'][4]['planet']=='Merkur'
        assert 'interpretation' not in first

    def test_invalid_annual_year_and_coordinates(self):
        from server import varshaphala
        request={'utc':'1985-11-04T00:15:00Z','latitude':45.45,'longitude':16.3667,'year':1984}
        with self.assertRaises(ValueError): varshaphala(request)
        with self.assertRaises(ValueError): varshaphala({**request,'year':2026,'latitude':100})
