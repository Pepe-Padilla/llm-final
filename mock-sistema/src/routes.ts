import { Router, Request, Response } from 'express';
import { PolizaData, ComprobacionPolizaRequest, ComprobacionPolizaResponse } from './types';

const router = Router();

// Función para manejar casos de fxprovicion
function handleFxProvision(poliza: PolizaData, res: Response): void {
  const fechaActual = new Date();
  const fechaCreacion = new Date(poliza.fechaCreacion);
  const diasTranscurridos = Math.floor((fechaActual.getTime() - fechaCreacion.getTime()) / (1000 * 60 * 60 * 24));
  
  console.log(`FX Provision - Póliza: ${poliza.poliza}, Estado: ${poliza.estadoPoliza}, Días: ${diasTranscurridos}`);
  
  if (poliza.estadoPoliza !== "en provision") {
    const respuesta: ComprobacionPolizaResponse = {
      "RESOLUCION AUTOMÁTICA": "cierre",
      "BUZON REASIGNACION": "",
      "SOLUCIÓN": "La póliza ya ha finalizado su tramitación y no se encuentra en estado de provisión"
    };
    res.status(200).json(respuesta);
    return;
  }
  
  if (diasTranscurridos > 15) {
    const respuesta: ComprobacionPolizaResponse = {
      "RESOLUCION AUTOMÁTICA": "manual",
      "BUZON REASIGNACION": "",
      "SOLUCIÓN": "La póliza lleva más de 15 días en provisión, requiere revisión manual"
    };
    res.status(200).json(respuesta);
    return;
  }
  
  const respuesta: ComprobacionPolizaResponse = {
    "RESOLUCION AUTOMÁTICA": "cierre",
    "BUZON REASIGNACION": "",
    "SOLUCIÓN": `La póliza aún está en fechas normales de provisión (${diasTranscurridos} días de 15 permitidos) y se resolverá dentro de la fecha estipulada`
  };
  res.status(200).json(respuesta);
}

// Función para manejar casos de disconformidad
function handleDisconformidad(poliza: PolizaData, res: Response): void {
  console.log(`Disconformidad - Póliza: ${poliza.poliza}, Estado: ${poliza.estadoPoliza}`);
  
  if (poliza.estadoPoliza !== "rechazada") {
    const respuesta: ComprobacionPolizaResponse = {
      "RESOLUCION AUTOMÁTICA": "cierre",
      "BUZON REASIGNACION": "",
      "SOLUCIÓN": `La póliza se encuentra en estado ${poliza.estadoPoliza}, no ha sido rechazada por lo que no procede la disconformidad`
    };
    res.status(200).json(respuesta);
    return;
  }
  
  // Si está rechazada, explicar el motivo
  const motivo = poliza.motivoRechazo || "No se especificó motivo de rechazo";
  const respuesta: ComprobacionPolizaResponse = {
    "RESOLUCION AUTOMÁTICA": "cierre",
    "BUZON REASIGNACION": "",
    "SOLUCIÓN": `Lamentamos informarle que su póliza ha sido rechazada. Motivo: ${motivo}. Si considera que esta decisión es incorrecta, puede presentar una nueva solicitud con la documentación requerida`
  };
  res.status(200).json(respuesta);
}

// Mock data con casos específicos para fxprovicion y disconformidad
const polizas: Record<string, PolizaData> = {
  "666023054-53-1": {
    poliza: "666023054-53-1",
    NIF: "44446321V",
    nombre: "MARIA TERESA GONZALEZ ESTEVEZ",
    tarjeta: "568016846",
    fechaNacimiento: "13/12/1971",
    estadoPoliza: "Derivada",
    fechaCreacion: "15/11/2024",
    motivoRechazo: ""
  },
  "666000001-56447147-0": {
    poliza: "666000001-56447147-0",
    NIF: "26804196L",
    nombre: "ALBERTO RIOJA CEPE",
    tarjeta: "123456789",
    fechaNacimiento: "01/01/1985",
    estadoPoliza: "Activa",
    fechaCreacion: "01/12/2024",
    motivoRechazo: ""
  },
  // Casos para fxprovicion
  "POL001-FX-PROVISION": {
    poliza: "POL001-FX-PROVISION",
    NIF: "12345678A",
    nombre: "JUAN CARLOS PROVISION TEST",
    tarjeta: "FX001234",
    fechaNacimiento: "15/03/1980",
    estadoPoliza: "en provision",
    fechaCreacion: "01/12/2024",
    motivoRechazo: ""
  },
  "POL002-FX-PROVISION-OLD": {
    poliza: "POL002-FX-PROVISION-OLD",
    NIF: "87654321B",
    nombre: "MARIA LUISA PROVISION OLD",
    tarjeta: "FX005678",
    fechaNacimiento: "20/05/1975",
    estadoPoliza: "en provision",
    fechaCreacion: "15/11/2024",
    motivoRechazo: ""
  },
  "POL003-FX-ACTIVA": {
    poliza: "POL003-FX-ACTIVA",
    NIF: "11223344C",
    nombre: "PEDRO GONZALEZ ACTIVA",
    tarjeta: "FX009876",
    fechaNacimiento: "10/07/1990",
    estadoPoliza: "activa",
    fechaCreacion: "20/11/2024",
    motivoRechazo: ""
  },
  // Casos para disconformidad  
  "POL004-DISCONF-RECHAZADA": {
    poliza: "POL004-DISCONF-RECHAZADA",
    NIF: "55667788D",
    nombre: "ANA MARIA DISCONFORMIDAD",
    tarjeta: "DC001234",
    fechaNacimiento: "25/09/1985",
    estadoPoliza: "rechazada",
    fechaCreacion: "10/11/2024",
    motivoRechazo: "Documentación incompleta: falta certificado médico actualizado y justificante de ingresos"
  },
  "POL005-DISCONF-ACTIVA": {
    poliza: "POL005-DISCONF-ACTIVA",
    NIF: "99887766E",
    nombre: "CARLOS ALBERTO DISCONFORMIDAD",
    tarjeta: "DC005678",
    fechaNacimiento: "12/01/1978",
    estadoPoliza: "activa",
    fechaCreacion: "25/11/2024",
    motivoRechazo: ""
  },
  "POL006-DISCONF-RECHAZADA": {
    poliza: "POL006-DISCONF-RECHAZADA",
    NIF: "33445566F",
    nombre: "LUCIA FERNANDEZ RECHAZO",
    tarjeta: "DC009876",
    fechaNacimiento: "03/06/1992",
    estadoPoliza: "rechazada",
    fechaCreacion: "05/11/2024",
    motivoRechazo: "No cumple requisitos de edad mínima para el producto contratado"
  },
  // Casos adicionales
  "POL007-CANCELADA": {
    poliza: "POL007-CANCELADA",
    NIF: "66778899G",
    nombre: "MIGUEL ANGEL CANCELADO",
    tarjeta: "CN001234",
    fechaNacimiento: "18/11/1983",
    estadoPoliza: "cancelada",
    fechaCreacion: "30/10/2024",
    motivoRechazo: ""
  },
  "POL008-BAJA": {
    poliza: "POL008-BAJA",
    NIF: "77889900H",
    nombre: "ELENA RODRIGUEZ BAJA",
    tarjeta: "BJ001234",
    fechaNacimiento: "22/04/1987",
    estadoPoliza: "baja",
    fechaCreacion: "15/10/2024",
    motivoRechazo: ""
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
  
  // Log para debugging
  console.log('Recibida petición comprobacionPoliza:', JSON.stringify(data, null, 2));
  
  // Extraer parámetros de manera flexible
  const polizaNum = data.poliza;
  const codSolucion = data.codSolucion || data.cod_solucion;
  
  // Buscar póliza
  const poliza = polizas[polizaNum];
  
  if (!poliza) {
    // Si no existe la póliza, respuesta por defecto
    const respuestaDefault: ComprobacionPolizaResponse = {
      "RESOLUCION AUTOMÁTICA": "manual",
      "BUZON REASIGNACION": "",
      "SOLUCIÓN": "Póliza no encontrada, revisar manualmente"
    };
    return res.status(200).json(respuestaDefault);
  }
  
  // Lógica específica según el código de solución
  if (codSolucion === 'fxprovicion') {
    return handleFxProvision(poliza, res);
  } else if (codSolucion === 'disconformidad') {
    return handleDisconformidad(poliza, res);
  }
  
  // Caso por defecto - respuestas aleatorias para otros casos
  const respuestas: ComprobacionPolizaResponse[] = [
    {
      "RESOLUCION AUTOMÁTICA": "cierre",
      "BUZON REASIGNACION": "",
      "SOLUCIÓN": "La reclamación por tiempos de procesamiento de póliza es rechazada por estar dentro de los límites, solo se puede reclamar tras pasar el tiempo estimado de resolución (7 días hábiles)"
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
  
  // Siempre devolver respuesta exitosa
  res.status(200).json(respuesta);
});

// Agregar endpoint alternativo para mayor flexibilidad
router.post('/comprobacion_poliza', (req: Request, res: Response) => {
  // Mismo comportamiento que comprobacionPoliza
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

export { router }; 