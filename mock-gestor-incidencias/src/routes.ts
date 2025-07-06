import { Router, Request, Response } from 'express';
import { Incidencia, PatchIncidenciaRequest, HistorialEntry } from './types';

const router = Router();

// Mock data
const incidencias: Incidencia[] = [
  {
    codIncidencia: "MOCK_INC0001",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "No puede leer los mensajes de reembolsos",
    solicitante: "MOCK_NAME",
    estado: "En curso",
    apertura: "01/01/2025 10:00:00 CEST",
    prioridad: "3 - Media",
    descripcion: "Error: Indica que los mensajes de aviso de reembolsos la letra aparece en blanco y no se ven bien, los ha tenido de copiar y pegar en documento de texto y ponerlo en negrita para leer mensaje NIF/NIE/Otros: MOCK_NIF Nombre y apellidos: MOCK_NAME Nº de Tarjeta: T: MOCK_CARD Nº de póliza: PO: MOCK_POLICY Fecha de nacimiento: 01/01/1980 Ramo: salud Día y Hora en que se produce el error:01/01/2025-10:00 Email y teléfono de contacto: mock@email.com-MOCK_PHONE",
    historial: [
      {
        Fecha: "02/01/2025 08:00:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: "MOCK_BUZON",
        buzonAsignado: "MOCK_BUZON",
        estado: "En espera",
        detalle: "Mensaje de ejemplo de historial."
      },
      {
        Fecha: "03/01/2025 08:00:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: "MOCK_CODE",
        NotasResolucion: "Mensaje de cierre automático de ejemplo.",
        buzonComentario: "GR_SAL_COMP_AUTORIZACIONES",
        buzonAsignado: "GR_SAL_COMP_AUTORIZACIONES",
        estado: "En curso",
        detalle: null
      },
      {
        Fecha: "04/01/2025 08:00:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: "MOCK_BUZON_CIERRE",
        buzonAsignado: "MOCK_BUZON",
        estado: "En curso",
        detalle: "Reapertura: Se adjunta evidencias del error, pop up avisos de reembolsos, la letra aparece en blanco"
      }
    ]
  },
  {
    codIncidencia: "MOCK_INC0002",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "ERROR AL ENVIAR AUTORIZACION",
    solicitante: "MOCK_NAME",
    estado: "En curso",
    apertura: "01/01/2025 10:00:00 CEST",
    prioridad: "3 - Media",
    descripcion: "ERROR AL ENVIAR AUTORIZACION 01/01/2025 10:00H Pantalla en que se produce el error: Al enviar. Contenedor: MOCK_WEB y App MOCK_APP Dispositivo: MOCK_BROWSER y MOCK_DEVICE Documentación: Talón en Captura de pantalla MOCK_NIF MOCK_NAME PO: MOCK_POLICY Email: mock@email.com Tel: MOCK_PHONE",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0003",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Error al cargar documentación general",
    solicitante: "MOCK_NAME",
    estado: "En curso",
    apertura: "02/01/2025 09:15:00 CEST",
    prioridad: "2 - Alta",
    descripcion: "No se puede visualizar la documentación general de la póliza. Error al intentar acceder a los documentos. NIF: MOCK_NIF Nombre: MOCK_NAME Póliza: MOCK_POLICY",
    historial: [
      {
        Fecha: "02/01/2025 10:30:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: "MOCK_BUZON",
        buzonAsignado: "MOCK_BUZON",
        estado: "En espera",
        detalle: "Se requiere verificación de permisos de acceso a documentos."
      },
      {
        Fecha: "02/01/2025 14:45:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: "MOCK_CODE",
        NotasResolucion: "Se ha verificado que el problema está relacionado con la versión del API de documentación.",
        buzonComentario: "MOCK_BUZON",
        buzonAsignado: "MOCK_BUZON_TECNICO",
        estado: "En curso",
        detalle: "Reasignación a equipo técnico para actualización de API."
      }
    ]
  },
  {
    codIncidencia: "MOCK_INC0004",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Problema con beneficiarios en reembolsos",
    solicitante: "MOCK_NAME",
    estado: "En espera",
    apertura: "02/01/2025 11:30:00 CEST",
    prioridad: "3 - Media",
    descripcion: "No se visualizan todos los beneficiarios en el módulo de reembolsos. Solo aparece el titular. NIF: MOCK_NIF Nombre: MOCK_NAME Póliza: MOCK_POLICY",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0005",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Error al adjuntar documentación",
    solicitante: "MOCK_NAME",
    estado: "En curso",
    apertura: "03/01/2025 14:20:00 CEST",
    prioridad: "2 - Alta",
    descripcion: "No se puede adjuntar documentación en el proceso de reembolso. El sistema muestra error al intentar subir archivos. NIF: MOCK_NIF Nombre: MOCK_NAME",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0006",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Problema con IBAN en reembolsos",
    solicitante: "MOCK_NAME",
    estado: "En curso",
    apertura: "03/01/2025 16:45:00 CEST",
    prioridad: "3 - Media",
    descripcion: "Error al validar el IBAN en el proceso de reembolso. El sistema indica que el formato es incorrecto. NIF: MOCK_NIF IBAN: MOCK_IBAN",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0007",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Error en tarjeta digital",
    solicitante: "MOCK_NAME",
    estado: "En espera",
    apertura: "04/01/2025 10:00:00 CEST",
    prioridad: "2 - Alta",
    descripcion: "No se puede visualizar la tarjeta digital. El sistema muestra error al intentar acceder. NIF: MOCK_NIF Nombre: MOCK_NAME",
    historial: [
      {
        Fecha: "04/01/2025 11:20:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: "GR_SAL_COMP_AUTORIZACIONES",
        buzonAsignado: "GR_SAL_COMP_AUTORIZACIONES",
        estado: "En espera",
        detalle: "Se ha identificado que el problema ocurre solo con tarjetas de tipo MOCK_TYPE."
      },
      {
        Fecha: "04/01/2025 15:30:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: null,
        NotasResolucion: "Se está trabajando en la actualización del componente de generación de tarjetas digitales.",
        buzonComentario: "MOCK_BUZON",
        buzonAsignado: "MOCK_BUZON_TECNICO",
        estado: "En curso",
        detalle: "Implementando solución para manejo de tarjetas MOCK_TYPE.",
        adjuntos: ["/api/adjuntos/imagen001.png", "/api/adjuntos/imagen002.png"]
      }
    ]
  },
  {
    codIncidencia: "MOCK_INC0008",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Problema con cuadro médico",
    solicitante: "MOCK_NAME",
    estado: "En espera",
    apertura: "04/01/2025 15:30:00 CEST",
    prioridad: "3 - Media",
    descripcion: "Error al acceder al cuadro médico público. Al seleccionar especialidad médica, se descarga archivo HTML en lugar de mostrar la página. NIF: MOCK_NIF",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0009",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Error en gestión de pólizas",
    solicitante: "MOCK_NAME",
    estado: "En espera",
    apertura: "05/01/2025 09:00:00 CEST",
    prioridad: "2 - Alta",
    descripcion: "No se pueden visualizar los datos de la póliza en el componente de gestión. Error al cargar la información. NIF: MOCK_NIF Póliza: MOCK_POLICY",
    historial: [
      {
        Fecha: "05/01/2025 10:15:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: "GR_SAL_COMP_AUTORIZACIONES",
        buzonAsignado: "GR_SAL_COMP_AUTORIZACIONES",
        estado: "En curso",
        detalle: "Se ha identificado que el problema está relacionado con la llamada al API searchByPolicy.",
        adjuntos: ["/api/adjuntos/imagen003.png"]
      },
      {
        Fecha: "05/01/2025 13:45:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: "GR_SAL_COMP_AUTORIZACIONES",
        buzonAsignado: "GR_SAL_COMP_AUTORIZACIONES",
        estado: "En espera",
        detalle: "Pendiente de confirmación de cambios en el API de MOCK_BUZON.",
        adjuntos: ["/api/adjuntos/imagen004.png", "/api/adjuntos/imagen005.png"]
      },
      {
        Fecha: "05/01/2025 16:30:00 CEST",
        Autor: "MOCK_NAME",
        CodigoResolucion: "MOCK_CODE",
        NotasResolucion: "Se requiere actualización del componente para adaptarse a la nueva versión del API.",
        buzonComentario: "GR_SAL_COMP_AUTORIZACIONES",
        buzonAsignado: "GR_SAL_COMP_AUTORIZACIONES",
        estado: "Pendiente implantar",
        detalle: "Se ha identificado la causa raíz y se está trabajando en la solución."
      }
    ]
  },
  {
    codIncidencia: "MOCK_INC0010",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Problema con autorizaciones",
    solicitante: "MOCK_NAME",
    estado: "En espera",
    apertura: "05/01/2025 11:45:00 CEST",
    prioridad: "3 - Media",
    descripcion: "Error al finalizar el proceso de autorización. El sistema muestra error inesperado al enviar la solicitud. NIF: MOCK_NIF",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0011",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Error en descarga de documentación",
    solicitante: "MOCK_NAME",
    estado: "En curso",
    apertura: "06/01/2025 13:20:00 CEST",
    prioridad: "2 - Alta",
    descripcion: "No se puede descargar la documentación de la póliza. Error al intentar acceder a los documentos. NIF: MOCK_NIF Póliza: MOCK_POLICY",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0012",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Problema con datos de asegurados",
    solicitante: "MOCK_NAME",
    estado: "En espera",
    apertura: "06/01/2025 16:00:00 CEST",
    prioridad: "3 - Media",
    descripcion: "Los datos de los asegurados aparecen intercambiados en la visualización. NIF: MOCK_NIF Póliza: MOCK_POLICY",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0013",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Error en validación de NIF",
    solicitante: "MOCK_NAME",
    estado: "En curso",
    apertura: "07/01/2025 10:30:00 CEST",
    prioridad: "2 - Alta",
    descripcion: "Error al validar el NIF/CIF en el proceso de reembolso. El sistema indica que el formato es incorrecto. NIF: MOCK_NIF",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0014",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Problema con PDF de tarjeta",
    solicitante: "MOCK_NAME",
    estado: "En espera",
    apertura: "07/01/2025 14:15:00 CEST",
    prioridad: "3 - Media",
    descripcion: "El PDF de la tarjeta digital se genera en blanco. No se visualiza ningún contenido. NIF: MOCK_NIF",
    historial: []
  },
  {
    codIncidencia: "MOCK_INC0015",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "Error en médico realizador",
    solicitante: "MOCK_NAME",
    estado: "En curso",
    apertura: "08/01/2025 09:45:00 CEST",
    prioridad: "2 - Alta",
    descripcion: "El campo de médico realizador no acepta caracteres especiales ni comillas. Error al intentar introducir el nombre. NIF: MOCK_NIF",
    historial: []
  }
];

// GET /api/incidencias?buzon=GR_SAL_COMP_AUTORIZACIONES
router.get('/incidencias', (req: Request, res: Response) => {
  const buzon = req.query.buzon as string;
  const incidenciasFiltradas = buzon 
    ? incidencias.filter(inc => inc.buzon === buzon)
    : incidencias;
  res.json(incidenciasFiltradas);
});

// PATCH /api/incidencias/:codIncidencia
router.patch('/incidencias/:codIncidencia', (req: Request, res: Response) => {
  const { codIncidencia } = req.params;
  const patchData: PatchIncidenciaRequest = req.body;
  
  const incidencia = incidencias.find(inc => inc.codIncidencia === codIncidencia);
  if (!incidencia) {
    return res.status(404).json({ error: 'Incidencia no encontrada' });
  }

  const now = new Date().toLocaleString('es-ES', { timeZone: 'Europe/Madrid' });
  
  switch (patchData.action) {
    case 'reasignar':
      if (!patchData.buzonDestino) {
        return res.status(400).json({ error: 'Se requiere buzonDestino para reasignar' });
      }
      incidencia.historial.push({
        Fecha: now,
        Autor: "Sistema Automático",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: incidencia.buzon,
        buzonAsignado: patchData.buzonDestino,
        estado: "En curso",
        detalle: patchData.detalle || "Reasignación automática"
      });
      incidencia.buzon = patchData.buzonDestino;
      break;

    case 'resolver':
      if (!patchData.notasResolucion) {
        return res.status(400).json({ error: 'Se requiere notasResolucion para resolver' });
      }
      incidencia.historial.push({
        Fecha: now,
        Autor: "Sistema Automático",
        CodigoResolucion: "AUTO",
        NotasResolucion: patchData.notasResolucion,
        buzonComentario: incidencia.buzon,
        buzonAsignado: "GR_SAL_COMP_CIERRE",
        estado: "Resuelta",
        detalle: null
      });
      incidencia.estado = "Resuelta";
      break;

    case 'en_espera':
      incidencia.historial.push({
        Fecha: now,
        Autor: "Sistema Automático",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: incidencia.buzon,
        buzonAsignado: incidencia.buzon,
        estado: "En espera",
        detalle: patchData.detalle || "Puesta en espera automática"
      });
      incidencia.estado = "En espera";
      break;

    case 'pendiente_implantar':
      incidencia.historial.push({
        Fecha: now,
        Autor: "Sistema Automático",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: incidencia.buzon,
        buzonAsignado: incidencia.buzon,
        estado: "Pendiente implantar",
        detalle: patchData.detalle || "Marcada como pendiente de implantación"
      });
      incidencia.estado = "Pendiente implantar";
      break;
  }

  res.json(incidencia);
});

// GET /api/adjuntos/:filename
router.get('/adjuntos/:filename', (req: Request, res: Response) => {
  const { filename } = req.params;
  
  // Los archivos se sirven automáticamente por express.static
  // Este endpoint solo maneja casos especiales si es necesario
  res.json({
    message: `Adjunto disponible: ${filename}`,
    url: `/api/adjuntos/${filename}`,
    tipo: "imagen"
  });
});

export { router }; 