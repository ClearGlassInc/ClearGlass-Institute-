export type ArtemisInstallStage = 'check_env' | 'resolve_dependencies' | 'prepare_backend' | 'configure_profiles' | 'verify_runtime' | 'complete'

export type ArtemisInstallProgress = {
  stage: ArtemisInstallStage
  percent: number
  detail: string
  complete: boolean
}

export const ARTEMIS_LOCAL_BACKEND_URL = 'http://127.0.0.1:8642'

export const installStages: ArtemisInstallStage[] = [
  'check_env',
  'resolve_dependencies',
  'prepare_backend',
  'configure_profiles',
  'verify_runtime',
  'complete'
]

export function createProgress(stage: ArtemisInstallStage, index: number, detail: string): ArtemisInstallProgress {
  return {
    stage,
    percent: Math.round(((index + 1) / installStages.length) * 100),
    detail,
    complete: stage === 'complete'
  }
}
