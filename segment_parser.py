import os
import time
import xml.etree.ElementTree as ET
import xbmcvfs
import xbmcaddon
import unicodedata

from utils import get_addon, log

def remap_nfs_path_for_write(path):
    """
    Attempt to remap NFS paths for write operations.
    Kodi's NFS client may strip subdirectories from mount paths during writes.
    This function tries different path variations to find one that works.
    
    Returns a list of path variations to try, starting with the original.
    """
    if not path.startswith('nfs://'):
        return [path]  # Not an NFS path, return as-is
    
    variations = [path]  # Always try original first
    
    # Try removing the first subdirectory after the server/path
    # e.g., nfs://server/Media/Kodi/file -> nfs://server/Kodi/file
    try:
        parts = path.split('/', 4)  # Split into: ['nfs:', '', 'server', 'Media', 'Kodi/file']
        if len(parts) >= 5:
            # Reconstruct without the first subdirectory
            remapped = f"{parts[0]}//{parts[2]}/{parts[4]}"
            variations.append(remapped)
            log(f"🔄 NFS path remap variation: {remapped}")
    except:
        pass
    
    # Try removing all subdirectories, going to root
    # e.g., nfs://server/Media/Kodi/file -> nfs://server/file
    try:
        parts = path.split('/')
        if len(parts) >= 4:
            # Keep protocol and server, use just filename
            filename = parts[-1]
            server_part = '/'.join(parts[:3])  # nfs://server
            root_path = f"{server_part}/{filename}"
            if root_path not in variations:
                variations.append(root_path)
                log(f"🔄 NFS path remap variation (root): {root_path}")
    except:
        pass
    
    return variations

def safe_file_write(path, content, is_bytes=False):
    """
    Safely write a file with NFS path remapping fallback.
    Tries multiple path variations if the initial write fails.
    
    Based on Kodi developer recommendations:
    - Use xbmcvfs.File() for VFS protocol handling
    - Check write() return value AND file existence as fallback
    - Don't manually strip paths; let Kodi's VFS handle translation
    
    Args:
        path: File path to write to
        content: Content to write (string or bytes)
        is_bytes: If True, content is already bytes; otherwise encode as UTF-8
    
    Returns:
        tuple: (success: bool, bytes_written: int or None)
    """
    if not is_bytes and isinstance(content, str):
        content_bytes = content.encode('utf-8')
    else:
        content_bytes = content
    
    # Get path variations to try (only for NFS)
    path_variations = remap_nfs_path_for_write(path)
    
    last_error = None
    for attempt_path in path_variations:
        try:
            log(f"📝 Attempting to write to: {attempt_path}")
            
            # For NFS, delete the file first to ensure clean overwrite
            # Kodi's NFS client may not properly truncate files on overwrite
            if attempt_path.startswith('nfs://') and xbmcvfs.exists(attempt_path):
                try:
                    log(f"🗑️ Deleting existing NFS file before write: {attempt_path}")
                    xbmcvfs.delete(attempt_path)
                    # Small delay to ensure deletion completes on NFS
                    time.sleep(0.1)
                except Exception as del_err:
                    log(f"⚠️ Could not delete existing file (may not exist): {del_err}")
            
            f = xbmcvfs.File(attempt_path, 'w')
            if not f:
                log(f"⚠️ Failed to create file object for: {attempt_path}")
                last_error = "Failed to create file object"
                continue
            
            # Write the content - write() may return bytes written, True, or None/False
            result = f.write(content_bytes)
            f.close()
            
            # Check if write was successful
            # Method 1: Check return value (bytes written or True)
            if result:
                # Verify file exists as fallback check (as recommended by Kodi dev)
                if xbmcvfs.exists(attempt_path):
                    # Try to set file permissions if enabled in settings
                    # Only works for local paths, not network VFS (nfs://, smb://)
                    try:
                        addon = get_addon()
                        set_permissions = addon.getSettingBool("set_file_permissions")
                        if set_permissions:
                            if not (attempt_path.startswith('nfs://') or attempt_path.startswith('smb://')):
                                try:
                                    # Set permissions to 666 (rw-rw-rw-) for maximum compatibility
                                    os.chmod(attempt_path, 0o666)
                                    log(f"🔐 Set file permissions to 666 (rw-rw-rw-) for: {attempt_path}")
                                except Exception as chmod_err:
                                    # chmod may fail on some filesystems or network mounts
                                    log(f"⚠️ Could not set file permissions (may be network mount): {chmod_err}")
                            else:
                                log(f"ℹ️ Skipping chmod for network path (permissions controlled by server): {attempt_path}")
                    except Exception as setting_err:
                        # If setting read fails, just continue (permission setting is optional)
                        log(f"⚠️ Could not read permission setting: {setting_err}")
                    
                    if attempt_path != path:
                        log(f"✅ Write succeeded with remapped path: {attempt_path} (original: {path})")
                    else:
                        log(f"✅ Write succeeded with original path: {path}")
                    return True, result if isinstance(result, int) else len(content_bytes)
                else:
                    log(f"⚠️ Write returned success but file doesn't exist: {attempt_path}")
                    # Continue to next variation
            else:
                # Method 2: write() returned None/False, but check if file exists anyway
                # (Sometimes Kodi's VFS succeeds but returns None)
                if xbmcvfs.exists(attempt_path):
                    # Try to set file permissions if enabled in settings
                    try:
                        addon = get_addon()
                        set_permissions = addon.getSettingBool("set_file_permissions")
                        if set_permissions:
                            if not (attempt_path.startswith('nfs://') or attempt_path.startswith('smb://')):
                                try:
                                    os.chmod(attempt_path, 0o666)
                                    log(f"🔐 Set file permissions to 666 (rw-rw-rw-) for: {attempt_path}")
                                except Exception as chmod_err:
                                    log(f"⚠️ Could not set file permissions (may be network mount): {chmod_err}")
                            else:
                                log(f"ℹ️ Skipping chmod for network path (permissions controlled by server): {attempt_path}")
                    except Exception as setting_err:
                        log(f"⚠️ Could not read permission setting: {setting_err}")
                    
                    log(f"✅ Write succeeded (file exists) despite None return: {attempt_path}")
                    if attempt_path != path:
                        log(f"✅ Using remapped path: {attempt_path} (original: {path})")
                    return True, len(content_bytes)
                else:
                    log(f"⚠️ Write returned no bytes and file doesn't exist: {attempt_path}")
                    # Check if this is an NFS error by examining the path
                    if attempt_path.startswith('nfs://') and attempt_path != path_variations[-1]:
                        log(f"🔄 NFS write failed, trying next path variation...")
                        continue
            
        except Exception as e:
            last_error = e
            error_msg = str(e)
            log(f"⚠️ Write exception for {attempt_path}: {error_msg}")
            
            # If this is an NFS-specific error and we have more variations, continue
            if ("NFS" in error_msg or "ACCESS denied" in error_msg or "NFS3ERR" in error_msg):
                if attempt_path != path_variations[-1]:  # Not the last variation
                    log(f"🔄 NFS error detected, trying next path variation...")
                    continue
            
            # For non-NFS errors or last variation, we'll break after logging
            if attempt_path == path_variations[-1]:
                break
    
    # All attempts failed
    if last_error:
        log(f"❌ All write attempts failed. Last error: {last_error}")
    else:
        log(f"❌ All write attempts failed. Write() returned None/False for all paths.")
        if path.startswith('nfs://'):
            log(f"⚠️ NFS write issue detected. Possible causes:")
            log(f"   1. NFS server permissions (check /etc/exports for 'rw' not 'ro')")
            log(f"   2. NFS server needs 'insecure' flag for non-privileged ports")
            log(f"   3. Path normalization issue in Kodi's NFS client")
    return False, None

def normalize_label(text):
    """Normalize and lowercase labels for consistent matching"""
    return unicodedata.normalize("NFKC", text or "").strip().lower()

def hms_to_seconds(hms):
    """Convert HH:MM:SS.mmm format to seconds"""
    parts = hms.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        return float(parts[0])

def seconds_to_hms(seconds):
    """Convert seconds to HH:MM:SS.mmm format"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def indent_xml(elem, level=0, indent="  "):
    """Manually indent XML element tree (Python 3.8 compatible)"""
    i = "\n" + level * indent
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + indent
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent_xml(child, level+1, indent)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

class SegmentItem:
    def __init__(self, start_seconds, end_seconds, label="segment", source="edl", action_type=None):
        if end_seconds < start_seconds:
            raise ValueError(f"Segment end time ({end_seconds}) must be after start time ({start_seconds})")
        
        self.start_seconds = start_seconds
        self.end_seconds = end_seconds
        self.source = source
        self.segment_type_label = normalize_label(label)
        self.action_type = action_type
        self.raw_label = label  # Keep original label for display
    
    def is_active(self, current_time):
        """Check if current time falls within segment bounds"""
        return self.start_seconds <= current_time <= self.end_seconds
    
    def get_duration(self):
        """Return duration of the segment"""
        return self.end_seconds - self.start_seconds
    
    def __str__(self):
        return f"{self.raw_label} [{self.start_seconds:.2f}-{self.end_seconds:.2f}]"

def safe_file_read(*paths):
    """Safely read a file, trying multiple paths"""
    for path in paths:
        if path:
            log(f"📂 Attempting to read: {path}")
            try:
                f = xbmcvfs.File(path)
                content = f.read()
                f.close()
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='replace')
                if content:
                    log(f"✅ Successfully read file: {path}")
                    return content
            except Exception as e:
                log(f"❌ Failed to read {path}: {e}")
    return None

def parse_chapters(video_path):
    """Parse chapter.xml file and return list of SegmentItem objects"""
    base = os.path.splitext(video_path)[0]
    video_dir = os.path.dirname(video_path)
    suffixes = ["-chapters.xml", "_chapters.xml", "-chapter.xml", "_chapter.xml"]
    
    paths_to_try = [f"{base}{s}" for s in suffixes]
    # Also check for "chapters.xml" in the same directory
    if video_dir:
        paths_to_try.append(os.path.join(video_dir, "chapters.xml"))
    
    log(f"🔍 Attempting chapter XML paths: {paths_to_try}")
    xml_data = safe_file_read(*paths_to_try)
    if not xml_data:
        log("🚫 No chapter XML file found")
        return None
    
    try:
        root = ET.fromstring(xml_data)
        result = []
        for atom in root.findall(".//ChapterAtom"):
            raw_label = atom.findtext(".//ChapterDisplay/ChapterString", default="")
            label = raw_label.strip() if raw_label else "segment"
            start = atom.findtext("ChapterTimeStart")
            end = atom.findtext("ChapterTimeEnd")
            if start and end:
                result.append(SegmentItem(
                    hms_to_seconds(start),
                    hms_to_seconds(end),
                    label,
                    source="xml"
                ))
                log(f"📘 Parsed XML segment: {start} → {end} | label='{label}'")
        
        if result:
            log(f"✅ Total segments parsed from XML: {len(result)}")
        return result if result else None
    except Exception as e:
        log(f"❌ XML parse failed: {e}")
    return None

def parse_edl(video_path):
    """Parse .edl file and return list of SegmentItem objects"""
    base = video_path.rsplit('.', 1)[0]
    paths_to_try = [f"{base}.edl"]
    
    log(f"🔍 Attempting EDL paths: {paths_to_try}")
    edl_data = safe_file_read(*paths_to_try)
    if not edl_data:
        log("🚫 No EDL file found")
        return []
    
    log(f"🧾 Raw EDL content:\n{edl_data}")
    
    segments = []
    try:
        for line in edl_data.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                try:
                    s = float(parts[0])
                    e = float(parts[1])
                    action = int(parts[2]) if len(parts) > 2 else 4
                    label = "segment"  # Default label
                    
                    # Try to get label from mapping if available
                    try:
                        addon = get_addon()
                        mapping = {}
                        raw = addon.getSetting("action_mapping")
                        if raw:
                            pairs = [entry.strip() for entry in raw.split(",") if ":" in entry]
                            for pair in pairs:
                                try:
                                    act, lbl = pair.split(":", 1)
                                    mapping[int(act.strip())] = lbl.strip()
                                except:
                                    pass
                        label = mapping.get(action, "segment")
                    except:
                        pass
                    
                    segments.append(SegmentItem(s, e, label, source="edl", action_type=action))
                    log(f"📗 Parsed EDL line: {s} → {e} | action={action} | label='{label}'")
                except (ValueError, IndexError) as e:
                    log(f"⚠️ Skipped invalid EDL line: {line} ({e})")
    except Exception as e:
        log(f"❌ EDL parse failed: {e}")
    
    log(f"✅ Total segments parsed from EDL: {len(segments)}")
    return segments

def save_chapters(video_path, segments):
    """Save segments to chapter.xml file"""
    # Handle path properly - remove extension
    if '.' in video_path:
        base = video_path.rsplit('.', 1)[0]
    else:
        base = video_path
    
    # Use the first suffix format found, or default to -chapters.xml
    suffixes = ["-chapters.xml", "_chapters.xml"]
    output_path = None
    
    # Check which file exists
    for suffix in suffixes:
        path = f"{base}{suffix}"
        if xbmcvfs.exists(path):
            output_path = path
            break
    
    # If no file exists, create new one with default suffix
    if not output_path:
        output_path = f"{base}{suffixes[0]}"
    
    log(f"💾 Saving {len(segments)} segments to: {output_path}")
    
    # Get action mapping from settings
    action_mapping = {}
    try:
        addon = get_addon()
        raw = addon.getSetting("action_mapping")
        if raw:
            pairs = [entry.strip() for entry in raw.split(",") if ":" in entry]
            for pair in pairs:
                try:
                    action_type, label = pair.split(":", 1)
                    action_mapping[int(action_type.strip())] = label.strip()
                except:
                    pass
    except:
        pass
    
    # Create XML structure
    root = ET.Element("Chapters")
    edition = ET.SubElement(root, "EditionEntry")
    
    for seg in segments:
        atom = ET.SubElement(edition, "ChapterAtom")
        ET.SubElement(atom, "ChapterTimeStart").text = seconds_to_hms(seg.start_seconds)
        ET.SubElement(atom, "ChapterTimeEnd").text = seconds_to_hms(seg.end_seconds)
        
        display = ET.SubElement(atom, "ChapterDisplay")
        # Use label from action mapping if available, otherwise use segment label
        if seg.action_type and seg.action_type in action_mapping:
            label = action_mapping[seg.action_type]
        else:
            label = seg.raw_label if hasattr(seg, 'raw_label') else seg.segment_type_label
        ET.SubElement(display, "ChapterString").text = label
    
    # Write to file
    try:
        # Ensure directory exists
        try:
            dir_path = '/'.join(output_path.split('/')[:-1])
            if dir_path and not xbmcvfs.exists(dir_path):
                log(f"📁 Creating directory: {dir_path}")
                xbmcvfs.mkdirs(dir_path)
        except Exception as dir_err:
            log(f"⚠️ Could not ensure directory exists: {dir_err}")
        
        # Manually indent XML (Python 3.8 compatible - ET.indent() requires Python 3.9+)
        indent_xml(root, indent="  ")
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Add XML declaration
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        
        log(f"📝 Writing XML content to: {output_path}")
        log(f"📝 XML content length: {len(xml_str)} bytes")
        
        # Use safe_file_write with NFS path remapping fallback
        success, bytes_written = safe_file_write(output_path, xml_str, is_bytes=False)
        
        if success:
            log(f"✅ Successfully saved chapter XML to: {output_path} ({bytes_written} bytes written)")
            return True
        else:
            log(f"❌ Failed to write chapter XML to: {output_path}")
            error_msg = "NFS path normalization issue or write permission denied"
            if "NFS" in str(output_path):
                log(f"⚠️ NFS write error detected. Tried multiple path variations.")
                log(f"⚠️ Solutions:")
                log(f"   1. Mount NFS share at OS level and add as local source in Kodi")
                log(f"   2. Use SMB instead of NFS if possible")
                log(f"   3. Check NFS server export settings (add 'insecure' option)")
            return False
    except Exception as e:
        log(f"❌ Failed to save chapter XML: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return False

def save_edl(video_path, segments):
    """Save segments to .edl file"""
    # Handle path properly - remove extension
    if '.' in video_path:
        base = video_path.rsplit('.', 1)[0]
    else:
        base = video_path
    output_path = f"{base}.edl"
    
    # Check if EDL file already exists - if so, use that exact path format
    # This ensures we use the path format that Kodi recognizes for writes
    if xbmcvfs.exists(output_path):
        log(f"📂 Existing EDL file found, using its path format: {output_path}")
    else:
        log(f"📂 EDL file does not exist, will create: {output_path}")
    
    log(f"💾 Saving {len(segments)} segments to: {output_path}")
    
    # Get action mapping from settings to reverse lookup label -> action_type
    label_to_action = {}
    try:
        addon = get_addon()
        raw = addon.getSetting("action_mapping")
        if raw:
            pairs = [entry.strip() for entry in raw.split(",") if ":" in entry]
            for pair in pairs:
                try:
                    action_type, label = pair.split(":", 1)
                    label_to_action[label.strip().lower()] = int(action_type.strip())
                except:
                    pass
    except:
        pass
    
    try:
        lines = []
        for seg in segments:
            # Determine action type: use existing, or lookup from label, or default to 4
            action = seg.action_type if seg.action_type else 4
            if not seg.action_type:
                # Try to find action type from label using reverse mapping
                seg_label = (seg.raw_label if hasattr(seg, 'raw_label') else seg.segment_type_label).lower()
                if seg_label in label_to_action:
                    action = label_to_action[seg_label]
                else:
                    action = 4  # Default action type
            lines.append(f"{seg.start_seconds:.3f}\t{seg.end_seconds:.3f}\t{action}")
        
        content = "\n".join(lines) + "\n"
        
        # Ensure directory exists
        try:
            dir_path = '/'.join(output_path.split('/')[:-1])
            if dir_path and not xbmcvfs.exists(dir_path):
                log(f"📁 Creating directory: {dir_path}")
                xbmcvfs.mkdirs(dir_path)
        except Exception as dir_err:
            log(f"⚠️ Could not ensure directory exists: {dir_err}")
        
        log(f"📝 Writing EDL content to: {output_path}")
        log(f"📝 EDL content length: {len(content)} bytes")
        log(f"📝 EDL content preview: {content[:100]}...")
        
        # Use safe_file_write with NFS path remapping fallback
        success, bytes_written = safe_file_write(output_path, content, is_bytes=False)
        
        if success:
            log(f"✅ Successfully saved EDL to: {output_path} ({bytes_written} bytes written)")
            return True
        else:
            log(f"❌ Failed to write EDL to: {output_path}")
            if "NFS" in str(output_path):
                log(f"⚠️ NFS write error detected. Tried multiple path variations.")
                log(f"⚠️ Solutions:")
                log(f"   1. Mount NFS share at OS level and add as local source in Kodi")
                log(f"   2. Use SMB instead of NFS if possible")
                log(f"   3. Check NFS server export settings (add 'insecure' option)")
            return False
    except Exception as e:
        log(f"❌ Failed to save EDL: {e}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return False

