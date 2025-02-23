from typing import List, Dict, Any, Optional
from todoist_api_python.api import TodoistAPI
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TodoistServices:
    def __init__(self, access_token: str):
        """Initialize with an access token from frontend"""
        self.api = TodoistAPI(access_token)
        
    def get_all_tasks(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active tasks, optionally filtered by project"""
        try:
            tasks = self.api.get_tasks(project_id=project_id)
            return [
                {
                    'id': task.id,
                    'content': task.content,
                    'description': task.description,
                    'project_id': task.project_id,
                    'section_id': task.section_id,
                    'parent_id': task.parent_id,
                    'priority': task.priority,
                    'due': {
                        'date': task.due.date if task.due else None,
                        'string': task.due.string if task.due else None,
                        'recurring': task.due.recurring if task.due else None
                    } if task.due else None,
                    'url': task.url,
                    'created_at': task.created_at,
                } for task in tasks
            ]
        except Exception as e:
            logger.error(f"Error fetching tasks: {str(e)}")
            raise

    def create_task(self, content: str, description: Optional[str] = None,
                   project_id: Optional[str] = None, due_string: Optional[str] = None,
                   priority: Optional[int] = None) -> Dict[str, Any]:
        """Create a new task"""
        try:
            task = self.api.add_task(
                content=content,
                description=description,
                project_id=project_id,
                due_string=due_string,
                priority=priority
            )
            return {
                'id': task.id,
                'content': task.content,
                'description': task.description,
                'project_id': task.project_id,
                'url': task.url,
                'created_at': task.created_at
            }
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise

    def update_task(self, task_id: str, content: Optional[str] = None,
                   description: Optional[str] = None, due_string: Optional[str] = None,
                   priority: Optional[int] = None) -> Dict[str, Any]:
        """Update an existing task"""
        try:
            task = self.api.update_task(
                task_id=task_id,
                content=content,
                description=description,
                due_string=due_string,
                priority=priority
            )
            return {
                'id': task.id,
                'content': task.content,
                'description': task.description,
                'project_id': task.project_id,
                'url': task.url,
                'updated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            raise

    def close_task(self, task_id: str) -> Dict[str, str]:
        """Close (complete) a task"""
        try:
            self.api.close_task(task_id=task_id)
            return {'status': 'success', 'message': f'Task {task_id} completed'}
        except Exception as e:
            logger.error(f"Error closing task: {str(e)}")
            raise

    def delete_task(self, task_id: str) -> Dict[str, str]:
        """Delete a task"""
        try:
            self.api.delete_task(task_id=task_id)
            return {'status': 'success', 'message': f'Task {task_id} deleted'}
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}")
            raise

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        try:
            projects = self.api.get_projects()
            return [
                {
                    'id': project.id,
                    'name': project.name,
                    'color': project.color,
                    'view_style': project.view_style,
                    'url': project.url,
                } for project in projects
            ]
        except Exception as e:
            logger.error(f"Error fetching projects: {str(e)}")
            raise

    def create_project(self, name: str, color: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project"""
        try:
            project = self.api.add_project(name=name, color=color)
            return {
                'id': project.id,
                'name': project.name,
                'color': project.color,
                'view_style': project.view_style,
                'url': project.url,
            }
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise 