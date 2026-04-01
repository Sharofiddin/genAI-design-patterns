import os
import re
import time
import hashlib
import requests
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Union, Any
from llama_index.core import Document
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages the local cache for downloaded files.
    Attributes:
      cache_dir (Path): Path to the cache directory
    """

    def __init__(self, cache_dir: str = "./.cache"):
        """
        Initialize the cache manager.
        Args:
          cache_dir (str): Path to the cache directory, Defaults to "./.cache"
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()
    def _ensure_cache_dir(self)-> None:
        """Create the cache directory if it doesn't exist."""
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True)
            logger.info(f"Created cache directory at {self.cache_dir}")
    def _get_cache_filename(self, url: str) -> str:
        """Generate a unique filename for a URL
           Args:
             url (str): The URL to generate a filename for.
          Returns:
             str: A unique file name based on the URL
        """

        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        original_filename = path_parts[-1] if path_parts[-1] else 'index'

        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        if '.' in original_filename:
            name_parts = original_filename.split('.')
            extension = name_parts[-1]
            base_name = '.'.join(name_parts[:-1])
            return f"{base_name}_{url_hash}.{extension}"
        else:
            return f"{original_filename}_{url_hash}.txt"
    def get_cache_path(self, url: str) -> Path:
        """Get the cache path for URL.
           Args:
             url (str): The URL to get the cache path for.
            Returns:
              Path: the path where the cache file would be stored.
        """
        file_name = self._get_cache_filename(url)
        return self.cache_dir / file_name
    
    def is_cached(self, url: str) -> bool:
        """
        Check if URL is already cached.

        Args:
          url(str) : The URL to check
        Returns:
           bool: True if the URL is cached, False otherwise.  
        """
        cache_path = self.get_cache_path(url)
        return cache_path.exists()
    def get_cached_context(self, url: str) -> Optional[str]:
        """
        Get the cached content for URL
        Args:
          url (str) - The URL to get cached content for.
        Returns:
          Optional[str]: The cached content if available , None otherewise
        """

        if not self.is_cached(url):
            return None
        cache_path = self.get_cache_path(url)
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Error reading cached file for {url}: {e}")
            return None
    def cache_content(self, url: str, content: str) -> bool:
        """
        Cache content for a url
        Args:
          url(str):  The URL the content was downloaded from
          content(str): The content to cache
        Returns:
          bool: True if content caching was successful, False otherwise.
        """
        self._ensure_cache_dir()
        cache_path = self.get_cache_path(url)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Cached content for {url} at {cache_path}")
            return True
        except Exception as e:
            logger.warning(f"Caching failed for {url}: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
          Clear all cached files
          Returns: 
             bool: True if clearing was successful, False otherwise
        """
        try:
            if self.cache_dir.exists():
                for file_path in self.cache_dir.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.warning(f"Cache clearing error: {e}")
            return False
    def get_cache_size(self) -> Tuple[int, str]:
        """
        Get the total size of the cache
        Returns:
          Tuple[int,str]: A tuple containing the size in bytes and a human-readable size.
        """
        total_size = 0
        if self.cache_dir.exists():
            for file_path in self.cache_dir.iterdir():
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        
        units = ['B', 'KB', 'MB', 'GB']
        size_human = total_size
        unit_index = 0
        while size_human > 1024 and unit_index < len(units) - 1:
            size_human /= 1024
            units += 1
        human_readable = f"{size_human:.2f} {units[unit_index]}"
        return total_size, human_readable
    def list_cached_files(self) -> List[Dict[str, Any]]:
        """
        List all cached files with metadata".
        Returns:
          List[Dict[str, Any]]: A list of dictionaries containing file information
        """

        files_info = []

        if self.cache_dir.exists():
            for file_path in self.cache_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files_info.append({
                        'filename': file_path.name,
                        'path': str(file_path),
                        'size_bytes': stat.st_size,
                        'last_modified': time.ctime(stat.st_mtime)
                    })
        return files_info

class GutenbergTextLoadError(Exception):
    """Exception raised for errors in loading Gutenberg text files."""
    pass
class DocumentSource(ABC):
    @classmethod
    @abstractmethod
    def load_from_url(self, url) -> Document:
        pass

class GutenbergSource(DocumentSource):
    """
    A class to load text files form Project Gutenberg as a LlamaIndex Document.

    This class handles fetching text content form URLs, processing Gutenberg-specific
    formatting, and creating a document store indexed by BM25

    Attributes:
      cache_manager (CacheManager): Manager for the local cache.
    """

    def __init__(self, cache_dir:str = "./.cache"):
        self.cache_manager = CacheManager(cache_dir)
    
