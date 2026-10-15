// Project identification is separate from numbered work evidence.
export const coverLabels={
 en:{facade:'Project facade',context:'Project identification photo',missing:'Facade photo not registered',issued:'Report generated',scope:'Report scope',overview:'Project overview',failed:'The project facade could not be loaded. Retry before saving the report.'},
 pt:{facade:'Fachada da obra',context:'Foto de identificação do projeto',missing:'Foto da fachada não cadastrada',issued:'Relatório gerado',scope:'Abrangência do relatório',overview:'Visão geral da obra',failed:'Não foi possível carregar a fachada da obra. Tente novamente antes de salvar o relatório.'}
};
export function facadePhotoURL(project){const url=project?.facadePhoto?.url||project?.reportCover?.url;return typeof url==='string'&&/^(https?:\/\/|data:image\/|blob:)/i.test(url)?url:'';}

export function coverPhotoLabels(project,language='en'){const base=coverLabels[language]||coverLabels.en;return !project?.facadePhoto?.url&&project?.reportCover?.kind==='site-plan'?{...base,facade:language==='pt'?'Planta de localização':'Site location plan',context:language==='pt'?'Diagrama de referência - sem escala':'Reference diagram - not to scale'}:base;}
