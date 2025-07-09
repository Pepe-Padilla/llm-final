import { Router, Request, Response } from 'express';
import { PolizaData, ComprobacionPolizaRequest, ComprobacionPolizaResponse } from './types';

const router = Router();

// Mock data
const polizas: Record<string, PolizaData> = {
  "666023054-53-1": {
    poliza: "666023054-53-1",
    NIF: "44446321V",
    nombre: "MARIA TERESA GONZALEZ ESTEVEZ",
    tarjeta: "568016846",
    fechaNacimiento: "13/12/1971",
    estadoPoliza: "Derivada"
  },
  "666000001-56447147-0": {
    poliza: "666000001-56447147-0",
    NIF: "26804196L",
    nombre: "ALBERTO RIOJA CEPE",
    tarjeta: "123456789",
    fechaNacimiento: "01/01/1985",
    estadoPoliza: "Activa"
  }
};

// GET /api/poliza/:numeroPoliza
router.get('/poliza/:numeroPoliza', (req: Request, res: Response) => {
  const { numeroPoliza } = req.params;
  const poliza = polizas[numeroPoliza];
  
  if (!poliza) {
    return res.status(404).json({ error: 'Póliza no encontrada' });
  }
  
  res.json(poliza);
});

// POST /api/comprobacionPoliza - Acepta cualquier parámetro
router.post('/comprobacionPoliza', (req: Request, res: Response) => {
  // Aceptar cualquier estructura de datos - no validar nada
  const data = req.body;
  
  // Simular diferentes respuestas aleatorias - siempre exitoso
  const respuestas: ComprobacionPolizaResponse[] = [
    {
      "RESOLUCION AUTOMÁTICA": "cierre",
      "BUZON REASIGNACION": "",
      "SOLUCIÓN": "La reclamación por tiempos de procesamiento de poliza es rechazada por estar dentro de los límites, solo se puede reclamar tras pasar el tiempo estimado de resolución (7 días habiles)"
    },
    {
      "RESOLUCION AUTOMÁTICA": "reasignacion",
      "BUZON REASIGNACION": "GR_SAL_COMP_CIERRE",
      "SOLUCIÓN": "La póliza requiere una revisión manual por parte del equipo de cierre"
    },
    {
      "RESOLUCION AUTOMÁTICA": "en espera",
      "BUZON REASIGNACION": "",
      "SOLUCIÓN": "Se requiere información adicional del cliente para proceder con la resolución"
    },
    {
      "RESOLUCION AUTOMÁTICA": "manual",
      "BUZON REASIGNACION": "",
      "SOLUCIÓN": "Caso complejo que requiere intervención manual del equipo de soporte"
    }
  ];
  
  // Seleccionar una respuesta aleatoria
  const respuesta = respuestas[Math.floor(Math.random() * respuestas.length)];
  
  res.json(respuesta);
});

// Agregar endpoint alternativo para mayor flexibilidad
router.post('/comprobacion_poliza', (req: Request, res: Response) => {
  // Mismo comportamiento que comprobacionPoliza
  router.handle(req, res);
});

export { router }; 