import unittest
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_process_data(self):
        response = self.client.post(
            "/process-data",
            json={"nombre": "EmpresaTest"}
        )
        self.assertEqual(response.status_code, 201)

        data = response.get_json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Registro creado")
        self.assertIn("id", data)

    def test_update_status(self):
        # Primero creamos una empresa
        self.client.post("/process-data", json={"nombre": "EmpresaTest2"})

        # Luego actualizamos su estado
        response = self.client.post(
            "/update-status",
            json={"nombre": "EmpresaTest2", "estado": "PROCESADO"}
        )
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Estado actualizado")
        self.assertEqual(data["estado"], "PROCESADO")

if __name__ == "__main__":
    unittest.main()
