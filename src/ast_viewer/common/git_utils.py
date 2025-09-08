"""Git utilities for cloning and managing repositories."""

import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)


class GitRepositoryError(Exception):
    """Exception raised for Git repository operations."""
    pass


class GitCloner:
    """Utility class for cloning Git repositories."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the GitCloner.
        
        Args:
            temp_dir: Directory to use for temporary clones. If None, uses system temp.
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
    def is_valid_github_url(self, url: str) -> bool:
        """Check if URL is a valid GitHub repository URL.
        
        Args:
            url: Repository URL to validate
            
        Returns:
            True if valid GitHub URL, False otherwise
        """
        if not url:
            return False
            
        try:
            parsed = urlparse(url)
            
            # Support both HTTPS and SSH GitHub URLs
            github_patterns = [
                r'^https://github\.com/[\w\.-]+/[\w\.-]+/?$',
                r'^git@github\.com:[\w\.-]+/[\w\.-]+\.git$',
                r'^https://github\.com/[\w\.-]+/[\w\.-]+\.git$'
            ]
            
            return any(re.match(pattern, url) for pattern in github_patterns)
            
        except Exception as e:
            logger.warning(f"Invalid URL format: {url}, error: {e}")
            return False
    
    def normalize_github_url(self, url: str) -> str:
        """Normalize GitHub URL to HTTPS format.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Normalized HTTPS URL
        """
        if not url:
            raise GitRepositoryError("Empty URL provided")
            
        url = url.strip()
        
        # Convert SSH to HTTPS
        if url.startswith('git@github.com:'):
            repo_path = url.replace('git@github.com:', '').replace('.git', '')
            url = f"https://github.com/{repo_path}"
        
        # Ensure .git suffix for cloning
        if not url.endswith('.git') and self.is_valid_github_url(url):
            url = f"{url}.git"
            
        return url
    
    def extract_repo_info(self, url: str) -> Tuple[str, str]:
        """Extract owner and repository name from GitHub URL.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo_name)
        """
        try:
            normalized_url = self.normalize_github_url(url)
            parsed = urlparse(normalized_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo_name = path_parts[1].replace('.git', '')
                return owner, repo_name
            else:
                raise GitRepositoryError(f"Cannot extract repository info from URL: {url}")
                
        except Exception as e:
            raise GitRepositoryError(f"Failed to extract repository info: {e}")
    
    def clone_repository(
        self,
        github_url: str,
        branch: Optional[str] = None,
        shallow_clone: bool = True,
        clone_depth: Optional[int] = 1
    ) -> str:
        """Clone a GitHub repository to a temporary directory.
        
        Args:
            github_url: GitHub repository URL
            branch: Specific branch to clone (default: main/master)
            shallow_clone: Whether to perform shallow clone
            clone_depth: Depth for shallow clone
            
        Returns:
            Path to the cloned repository
            
        Raises:
            GitRepositoryError: If cloning fails
        """
        if not self.is_valid_github_url(github_url):
            raise GitRepositoryError(f"Invalid GitHub URL: {github_url}")
        
        try:
            # Normalize URL
            normalized_url = self.normalize_github_url(github_url)
            
            # Extract repository info for directory naming
            owner, repo_name = self.extract_repo_info(normalized_url)
            
            # Create unique temporary directory
            clone_dir = os.path.join(
                self.temp_dir, 
                f"ast_viewer_clone_{owner}_{repo_name}"
            )
            
            # Remove existing directory if it exists
            if os.path.exists(clone_dir):
                logger.info(f"Removing existing clone directory: {clone_dir}")
                shutil.rmtree(clone_dir)
            
            # Build git clone command
            cmd = ["git", "clone"]
            
            if shallow_clone and clone_depth:
                cmd.extend(["--depth", str(clone_depth)])
            
            if branch:
                cmd.extend(["--branch", branch])
            
            cmd.extend([normalized_url, clone_dir])
            
            logger.info(f"Cloning repository: {normalized_url} to {clone_dir}")
            
            # Execute git clone
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                error_msg = f"Git clone failed: {result.stderr}"
                logger.error(error_msg)
                raise GitRepositoryError(error_msg)
            
            logger.info(f"Successfully cloned repository to: {clone_dir}")
            return clone_dir
            
        except subprocess.TimeoutExpired:
            raise GitRepositoryError("Git clone operation timed out (5 minutes)")
        except Exception as e:
            raise GitRepositoryError(f"Failed to clone repository: {e}")
    
    def cleanup_clone(self, clone_path: str) -> None:
        """Clean up cloned repository directory.
        
        Args:
            clone_path: Path to the cloned repository to remove
        """
        try:
            if os.path.exists(clone_path):
                logger.info(f"Cleaning up clone directory: {clone_path}")
                shutil.rmtree(clone_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup clone directory {clone_path}: {e}")
    
    def get_repository_stats(self, clone_path: str) -> dict:
        """Get basic statistics about the cloned repository.
        
        Args:
            clone_path: Path to the cloned repository
            
        Returns:
            Dictionary with repository statistics
        """
        try:
            stats = {
                "total_files": 0,
                "python_files": 0,
                "javascript_files": 0,
                "typescript_files": 0,
                "total_size_bytes": 0,
                "languages": set()
            }
            
            for root, dirs, files in os.walk(clone_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        stats["total_size_bytes"] += file_size
                        stats["total_files"] += 1
                        
                        # Count by extension
                        extension = Path(file).suffix.lower()
                        if extension == '.py':
                            stats["python_files"] += 1
                            stats["languages"].add("python")
                        elif extension == '.js':
                            stats["javascript_files"] += 1
                            stats["languages"].add("javascript")
                        elif extension in ['.ts', '.tsx']:
                            stats["typescript_files"] += 1
                            stats["languages"].add("typescript")
                        elif extension == '.go':
                            stats["languages"].add("go")
                        elif extension == '.rs':
                            stats["languages"].add("rust")
                            
                    except OSError:
                        continue
            
            # Convert set to list for JSON serialization
            stats["languages"] = list(stats["languages"])
            
            return stats
            
        except Exception as e:
            logger.warning(f"Failed to get repository stats: {e}")
            return {"error": str(e)}


# Global instance for use across the application
git_cloner = GitCloner()


def clone_github_repository(
    github_url: str,
    branch: Optional[str] = None,
    shallow_clone: bool = True,
    clone_depth: Optional[int] = 1
) -> str:
    """Convenience function to clone a GitHub repository.
    
    Args:
        github_url: GitHub repository URL
        branch: Specific branch to clone
        shallow_clone: Whether to perform shallow clone
        clone_depth: Depth for shallow clone
        
    Returns:
        Path to the cloned repository
    """
    return git_cloner.clone_repository(
        github_url=github_url,
        branch=branch,
        shallow_clone=shallow_clone,
        clone_depth=clone_depth
    )


def cleanup_repository(clone_path: str) -> None:
    """Convenience function to cleanup a cloned repository.
    
    Args:
        clone_path: Path to the repository to cleanup
    """
    git_cloner.cleanup_clone(clone_path)


def validate_github_url(url: str) -> bool:
    """Convenience function to validate GitHub URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid GitHub URL
    """
    return git_cloner.is_valid_github_url(url)
