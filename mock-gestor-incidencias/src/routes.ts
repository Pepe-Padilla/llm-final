import { Router, Request, Response } from 'express';
import { Incidencia, PatchIncidenciaRequest, HistorialEntry } from './types';

const router = Router();

// Mock data
const incidencias: Incidencia[] = [
  {
    codIncidencia: "INC0176438",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "No puede leer los mensajes de reembolsos",
    solicitante: "ROSA MARIA VEGA RODRIGUEZ",
    estado: "En curso",
    apertura: "23/05/2025 14:43:45 CEST",
    prioridad: "3 - Media",
    descripcion: "Error: Indica que los mensajes de aviso de reembolsos la letra aparece en blanco y no se ven bien, los ha tenido de copiar y pegar en documento de texto y ponerlo en negrita para leer mensaje NIF/NIE/Otros: 44446321V Nombre y apellidos: MARIA TERESA GONZALEZ ESTEVEZ Nº de Tarjeta: T: 568016846 Nº de póliza: PO: 666023054-53-1 Fecha de nacimiento: 13/12/1971 Ramo: salud Día y Hora en que se produce el error:22/05/2025-16:46 Email y teléfono de contacto: magoe1971@GMAIL.COM-630151240",
    historial: [
      {
        Fecha: "26/05/2025 08:08:10 CEST",
        Autor: "Celia Jiménez de Andrés",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: "GR_SAL_COMP_AUTORIZACIONES",
        buzonAsignado: "GR_SAL_COMP_AUTORIZACIONES",
        estado: "En espera",
        detalle: "Buenos dias,\n\nHemos revisado la incidencia y no vemos a que se refiere el solicitante con la letra apareciendo en blanco, ya que no vemos que en las notificaciones la letra salga asi. ¿Podeis adjuntarnos una captura del error para que podamos identificar el problema?\n\nGracias y un saludo"
      },
      {
        Fecha: "28/05/2025 08:05:40 CEST",
        Autor: "Celia Jiménez de Andrés",
        CodigoResolucion: "851315",
        NotasResolucion: "Buenas,\nTras no recibir respuesta y haber realizado los tres strikes, procedemos a cerrar la incidencia.\nUn saludo",
        buzonComentario: "GR_SAL_COMP_AUTORIZACIONES",
        buzonAsignado: "GR_SAL_COMP_CIERRE",
        estado: "Resuelta",
        detalle: null
      },
      {
        Fecha: "29/05/2025 08:26:10 CEST",
        Autor: "ROSA MARIA VEGA RODRIGUEZ",
        CodigoResolucion: null,
        NotasResolucion: null,
        buzonComentario: "GR_SAL_COMP_CIERRE",
        buzonAsignado: "GR_SAL_COMP_AUTORIZACIONES",
        estado: "En curso",
        detalle: "Reapertura: Se adjunta evidencias del error, pop up avissos de reembolsos, la letra aparece en blanco"
      }
    ]
  },
  {
    codIncidencia: "INC0176098",
    buzon: "GR_SAL_COMP_AUTORIZACIONES",
    titulo: "ERROR AL ENVIAR AUTORIZACION",
    solicitante: "ROSA MARIA VEGA RODRIGUEZ",
    estado: "En curso",
    apertura: "23/05/2025 14:43:45 CEST",
    prioridad: "3 - Media",
    descripcion: "ERROR AL ENVIAR AUTORIZACION 23/05/2025 10:48H Pantalla en que se produce el error: Al enviar. Contenedor: SCA web y App S&B Dispositivo: Chrome y Iphone Documentación: Talón en Captura de pantalla 26804196L Alberto Rioja Cepe PO: 666000001-56447147-0 Email: betorc85@gmail.com Tel: 615 55 10 22",
    historial: []
  }
];

// GET /api/incidencias?buzon=GR_SAL_COMP_AUTORIZACIONES
router.get('/incidencias', (req: Request, res: Response) => {
  const buzon = req.query.buzon as string;
  const incidenciasFiltradas = incidencias.filter(inc => inc.buzon === buzon);
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

export { router }; 