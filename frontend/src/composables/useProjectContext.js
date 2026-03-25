import { useRoute } from 'vue-router';

/**
 * Composable che espone pid, projectSlug e projectId
 * letti da localStorage e dai parametri della rotta.
 */
export function useProjectContext() {
    const route = useRoute();
    const pid = localStorage.getItem('prolific_pid');
    const projectSlug = route.params.projectSlug ?? localStorage.getItem('project_slug');
    const projectId = localStorage.getItem('project_id');
    return { pid, projectSlug, projectId };
}
