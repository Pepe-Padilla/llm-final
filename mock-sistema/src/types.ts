export interface PolizaData {
  poliza: string;
  NIF: string;
  nombre: string;
  tarjeta: string;
  fechaNacimiento: string;
  estadoPoliza: string;
}

export interface ComprobacionPolizaRequest {
  poliza: string;
  codSolucion: string;
  strJson: string;
}

export interface ComprobacionPolizaResponse {
  "RESOLUCION AUTOMÁTICA": "cierre" | "reasignacion" | "en espera" | "manual";
  "BUZON REASIGNACION": string;
  "SOLUCIÓN": string;
} 