from typing import List, Dict, Any, Optional
import asana
import logging

logger = logging.getLogger(__name__)

class AsanaServices:
    def __init__(self, access_token: str):
        """Initialize with an access token from frontend"""
        self.client = asana.Client.access_token(access_token)
        # Return responses as dictionaries
        self.client.headers = {'asana-enable': 'new_user_task_lists'}
        
    def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get all workspaces"""
        try:
            return list(self.client.workspaces.get_workspaces())
        except Exception as e:
            logger.error(f"Error fetching workspaces: {str(e)}")
            raise

    def get_projects(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """Get all projects in a workspace"""
        try:
            return list(self.client.projects.get_projects({'workspace': workspace_gid}))
        except Exception as e:
            logger.error(f"Error fetching projects: {str(e)}")
            raise

    def get_tasks(self, project_gid: str) -> List[Dict[str, Any]]:
        """Get all tasks in a project"""
        try:
            return list(self.client.tasks.get_tasks({'project': project_gid}))
        except Exception as e:
            logger.error(f"Error fetching tasks: {str(e)}")
            raise

    def create_task(self, 
                   name: str,
                   workspace_gid: str,
                   project_gid: Optional[str] = None,
                   notes: Optional[str] = None,
                   due_on: Optional[str] = None,
                   assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create a new task"""
        try:
            task_data = {
                'name': name,
                'workspace': workspace_gid,
                'notes': notes,
                'due_on': due_on,
                'assignee': assignee
            }
            if project_gid:
                task_data['projects'] = [project_gid]

            return self.client.tasks.create_task(task_data)
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise

    def update_task(self,
                   task_gid: str,
                   name: Optional[str] = None,
                   notes: Optional[str] = None,
                   due_on: Optional[str] = None,
                   assignee: Optional[str] = None) -> Dict[str, Any]:
        """Update an existing task"""
        try:
            task_data = {}
            if name is not None:
                task_data['name'] = name
            if notes is not None:
                task_data['notes'] = notes
            if due_on is not None:
                task_data['due_on'] = due_on
            if assignee is not None:
                task_data['assignee'] = assignee

            return self.client.tasks.update_task(task_gid, task_data)
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            raise

    def delete_task(self, task_gid: str) -> None:
        """Delete a task"""
        try:
            self.client.tasks.delete_task(task_gid)
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}")
            raise

    def create_project(self, 
                      name: str,
                      workspace_gid: str,
                      notes: Optional[str] = None,
                      team: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project"""
        try:
            project_data = {
                'name': name,
                'workspace': workspace_gid,
                'notes': notes
            }
            if team:
                project_data['team'] = team

            return self.client.projects.create_project(project_data)
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise

    def get_sections(self, project_gid: str) -> List[Dict[str, Any]]:
        """Get all sections in a project"""
        try:
            return list(self.client.sections.get_sections_for_project(project_gid))
        except Exception as e:
            logger.error(f"Error fetching sections: {str(e)}")
            raise 