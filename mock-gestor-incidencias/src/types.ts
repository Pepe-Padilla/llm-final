export interface HistorialEntry {
  Fecha: string;
  Autor: string;
  CodigoResolucion: string | null;
  NotasResolucion: string | null;
  buzonComentario: string;
  buzonAsignado: string;
  estado: string;
  detalle: string | null;
  adjuntos?: string[];
}

export interface Incidencia {
  codIncidencia: string;
  buzon: string;
  titulo: string;
  solicitante: string;
  estado: string;
  apertura: string;
  prioridad: string;
  descripcion: string;
  historial: HistorialEntry[];
}

export interface PatchIncidenciaRequest {
  action: 'reasignar' | 'resolver' | 'en_espera' | 'pendiente_implantar';
  buzonDestino?: string;
  notasResolucion?: string;
  detalle?: string;
} 