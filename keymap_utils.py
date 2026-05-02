"""Keymap generation helpers.

Replaces the previous regex-on-XML approach with ElementTree. User comments
are preserved on Python versions that support ``TreeBuilder(insert_comments)``,
and unrelated key bindings are kept intact. CDATA is not round-tripped by the
stdlib XML writer; Kodi keymaps should not need CDATA for keyboard bindings.
"""
import os
import xml.etree.ElementTree as ET

import xbmc
import xbmcvfs

from utils import get_addon, log, log_always, log_error

ADDON_ID = "service.segmenteditor"
RUN_SCRIPT = f"RunScript({ADDON_ID})"

# Sections we want to bind the shortcut under. Global is optional but gives
# the broadest coverage; the other two are what actually fire during playback.
TARGET_SECTIONS = ("global", "FullscreenVideo", "VideoOSD")


def _translate_userdata_path():
    try:
        return xbmcvfs.translatePath("special://userdata")
    except Exception:
        try:
            return xbmc.translatePath("special://userdata")  # legacy
        except Exception:
            return None


def _load_or_create_tree(keymap_file):
    """Return an ElementTree rooted at <keymap>, creating a new one if needed."""
    if xbmcvfs.exists(keymap_file):
        try:
            f = xbmcvfs.File(keymap_file, "r")
            data = f.read()
            f.close()
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace")
            if data.strip():
                try:
                    parser = ET.XMLParser(
                        target=ET.TreeBuilder(insert_comments=True)
                    )
                except TypeError:
                    parser = None
                root = ET.fromstring(data, parser=parser)
                if root.tag != "keymap":
                    # Wrap an unexpected root into a fresh keymap.
                    new_root = ET.Element("keymap")
                    new_root.append(root)
                    return ET.ElementTree(new_root)
                return ET.ElementTree(root)
        except Exception as err:
            log_error(f"Existing keymap.xml is invalid, creating a new one: {err}")

    return ET.ElementTree(ET.Element("keymap"))


def _first_child(parent, tag):
    for child in list(parent):
        if child.tag == tag:
            return child
    return None


def _ensure_child(parent, tag):
    child = _first_child(parent, tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    return child


def _remove_stale_bindings(keyboard_elem, shortcut_key):
    """Remove any previous bindings for our addon that don't match the key."""
    for child in list(keyboard_elem):
        text = (child.text or "").strip()
        if RUN_SCRIPT not in text:
            continue
        mod = (child.attrib.get("mod") or "").lower()
        if child.tag == shortcut_key and mod == "ctrl":
            continue
        log(f"Removing stale keymap binding: <{child.tag} mod='{mod}'>{text}")
        keyboard_elem.remove(child)


def _ensure_binding(keyboard_elem, shortcut_key):
    """Ensure a single <shortcut mod='ctrl'>RunScript(...)</shortcut> exists."""
    for child in list(keyboard_elem):
        if (
            child.tag == shortcut_key
            and (child.attrib.get("mod") or "").lower() == "ctrl"
            and (child.text or "").strip() == RUN_SCRIPT
        ):
            return False  # already present
    binding = ET.SubElement(keyboard_elem, shortcut_key)
    binding.set("mod", "ctrl")
    binding.text = RUN_SCRIPT
    return True


def _indent(elem, level=0, spacer="  "):
    i = "\n" + level * spacer
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + spacer
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            _indent(child, level + 1, spacer)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def update_keymap_file():
    """Write (or rewrite) the userdata keymap.xml with our CTRL+<key> binding.

    Returns True on success, False on any kind of failure.
    """
    try:
        addon = get_addon()
        shortcut_key = (addon.getSetting("editor_shortcut_key") or "").strip().lower()
        if not shortcut_key or len(shortcut_key) != 1 or not shortcut_key.isalnum():
            log_always(f"Invalid shortcut key {shortcut_key!r}, falling back to 'e'")
            shortcut_key = "e"

        userdata = _translate_userdata_path()
        if not userdata:
            log_error("Could not resolve special://userdata")
            return False

        keymaps_dir = os.path.join(userdata, "keymaps")
        keymap_file = os.path.join(keymaps_dir, "keymap.xml")

        if not xbmcvfs.exists(keymaps_dir):
            try:
                xbmcvfs.mkdirs(keymaps_dir)
                log(f"Created keymaps directory: {keymaps_dir}")
            except Exception as mkdir_err:
                log_error(f"Could not create keymaps directory: {mkdir_err}")
                return False

        tree = _load_or_create_tree(keymap_file)
        root = tree.getroot()
        changed = False

        for section_name in TARGET_SECTIONS:
            section = _ensure_child(root, section_name)
            keyboard = _ensure_child(section, "keyboard")
            before = len(list(keyboard))
            _remove_stale_bindings(keyboard, shortcut_key)
            added = _ensure_binding(keyboard, shortcut_key)
            after = len(list(keyboard))
            if added or before != after:
                changed = True
                log(f"Updated <{section_name}><keyboard> with CTRL+{shortcut_key}")

        if not changed and xbmcvfs.exists(keymap_file):
            log(f"Keymap already up to date for CTRL+{shortcut_key}")
            return True

        _indent(root)
        xml_bytes = ET.tostring(root, encoding="utf-8")
        # ET.tostring omits the XML declaration when encoding='utf-8'; prepend it.
        content = b'<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes + b"\n"

        try:
            f = xbmcvfs.File(keymap_file, "w")
            if not f:
                log_error(f"Could not open keymap file for writing: {keymap_file}")
                return False
            result = f.write(content)
            f.close()
            if result or xbmcvfs.exists(keymap_file):
                log_always(f"Updated keymap file ({keymap_file}) with CTRL+{shortcut_key}")
                return True
            log_error("Write returned no bytes for keymap file")
            return False
        except Exception as write_err:
            log_error(f"Could not write keymap file: {write_err}")
            return False

    except Exception as err:
        log_error(f"Error updating keymap file: {err}")
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")
        return False
