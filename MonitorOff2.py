import ctypes
from ctypes import wintypes
import sys
import os

# ============================================================
#
# Monitor Off
#
# Windows 10 / 11
#
# Rattle & Sparky
#
# ============================================================

user32 = ctypes.WinDLL("user32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ------------------------------------------------------------
# WinAPI function signatures
# ------------------------------------------------------------

user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]

user32.DefWindowProcW.restype = ctypes.c_ssize_t

user32.SendMessageW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]

user32.SendMessageW.restype = ctypes.c_ssize_t

user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]

user32.GetMessageW.restype = wintypes.BOOL

user32.LoadImageW.argtypes = [
    wintypes.HINSTANCE,
    wintypes.LPCWSTR,
    wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]

user32.LoadImageW.restype = wintypes.HANDLE

# ------------------------------------------------------------
# Windows types
# ------------------------------------------------------------

LRESULT = ctypes.c_ssize_t
HCURSOR = wintypes.HANDLE
HBRUSH = wintypes.HANDLE
HICON = wintypes.HANDLE
HINSTANCE = wintypes.HANDLE

# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------

WM_DESTROY = 0x0002
WM_SYSCOMMAND = 0x0112

WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205

SC_MONITORPOWER = 0xF170

HWND_BROADCAST = 0xFFFF

MONITOR_OFF = 2

WM_TRAY = 0x8001

NIM_ADD = 0x00000000
NIM_DELETE = 0x00000002

NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004

MF_STRING = 0x00000000

TPM_LEFTALIGN = 0x0000
TPM_BOTTOMALIGN = 0x0020

IMAGE_ICON = 1

LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040

# ------------------------------------------------------------
# Structures
# ------------------------------------------------------------

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", HICON),

        ("szTip", wintypes.WCHAR * 128),

        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),

        ("szInfo", wintypes.WCHAR * 256),

        ("uTimeout", wintypes.UINT),

        ("szInfoTitle", wintypes.WCHAR * 64),

        ("dwInfoFlags", wintypes.DWORD),

        ("guidItem", ctypes.c_byte * 16),

        ("hBalloonIcon", HICON),
    ]


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),

        ("lpfnWndProc", ctypes.c_void_p),

        ("cbClsExtra", ctypes.c_int),

        ("cbWndExtra", ctypes.c_int),

        ("hInstance", HINSTANCE),

        ("hIcon", HICON),

        ("hCursor", HCURSOR),

        ("hbrBackground", HBRUSH),

        ("lpszMenuName", wintypes.LPCWSTR),

        ("lpszClassName", wintypes.LPCWSTR),
    ]


# ------------------------------------------------------------
# Globals
# ------------------------------------------------------------

tray_data = None
tray_icon_handle = None

# ------------------------------------------------------------
# Find bundled files
# ------------------------------------------------------------

def resource_path(filename):
    """
    Works both when running normally and
    when compiled with PyInstaller --onefile.
    """

    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(
            os.path.abspath(__file__)
        )

    return os.path.join(
        base_path,
        filename
    )


# ------------------------------------------------------------
# Monitor OFF
# ------------------------------------------------------------

def monitor_off():

    user32.SendMessageW(
        HWND_BROADCAST,
        WM_SYSCOMMAND,
        SC_MONITORPOWER,
        MONITOR_OFF
    )


# ------------------------------------------------------------
# Tray icon
# ------------------------------------------------------------

def add_tray_icon(hwnd):

    global tray_data
    global tray_icon_handle

    icon_path = resource_path("MonitorOff.ico")

    # Load our custom icon
    tray_icon_handle = user32.LoadImageW(
        None,
        icon_path,
        IMAGE_ICON,
        32,
        32,
        LR_LOADFROMFILE | LR_DEFAULTSIZE
    )

    if not tray_icon_handle:

        error = ctypes.get_last_error()

        print(
            f"Could not load tray icon: {error}"
        )

        return False

    tray_data = NOTIFYICONDATAW()

    tray_data.cbSize = ctypes.sizeof(
        NOTIFYICONDATAW
    )

    tray_data.hWnd = hwnd

    tray_data.uID = 1

    tray_data.uFlags = (
        NIF_MESSAGE |
        NIF_ICON |
        NIF_TIP
    )

    tray_data.uCallbackMessage = WM_TRAY

    tray_data.hIcon = tray_icon_handle

    tray_data.szTip = "Monitor Off"

    result = shell32.Shell_NotifyIconW(
        NIM_ADD,
        ctypes.byref(tray_data)
    )

    if not result:

        print(
            "Shell_NotifyIconW(NIM_ADD) failed"
        )

        return False

    return True


def remove_tray_icon():

    global tray_data
    global tray_icon_handle

    if tray_data is not None:

        shell32.Shell_NotifyIconW(
            NIM_DELETE,
            ctypes.byref(tray_data)
        )

        tray_data = None

    if tray_icon_handle:

        user32.DestroyIcon(
            tray_icon_handle
        )

        tray_icon_handle = None


# ------------------------------------------------------------
# Context menu
# ------------------------------------------------------------

def show_menu(hwnd):

    menu = user32.CreatePopupMenu()

    if not menu:
        return

    EXIT_ID = 1001

    user32.AppendMenuW(
        menu,
        MF_STRING,
        EXIT_ID,
        "Изход"
    )

    point = POINT()

    user32.GetCursorPos(
        ctypes.byref(point)
    )

    user32.SetForegroundWindow(
        hwnd
    )

    command = user32.TrackPopupMenu(
        menu,
        TPM_LEFTALIGN | TPM_BOTTOMALIGN,
        point.x,
        point.y,
        0,
        hwnd,
        None
    )

    user32.DestroyMenu(
        menu
    )

    # Important for tray popup menus
    user32.PostMessageW(
        hwnd,
        0,
        0,
        0
    )

    if command == EXIT_ID:

        user32.DestroyWindow(
            hwnd
        )


# ------------------------------------------------------------
# Window procedure
# ------------------------------------------------------------

WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
)


@WNDPROC
def wnd_proc(
    hwnd,
    msg,
    wparam,
    lparam
):

    if msg == WM_TRAY:

        if lparam == WM_LBUTTONUP:

            monitor_off()

            return 0

        elif lparam == WM_RBUTTONUP:

            show_menu(hwnd)

            return 0

    elif msg == WM_DESTROY:

        remove_tray_icon()

        user32.PostQuitMessage(
            0
        )

        return 0

    return user32.DefWindowProcW(
        hwnd,
        msg,
        wparam,
        lparam
    )


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    hInstance = kernel32.GetModuleHandleW(
        None
    )

    class_name = "RattleMonitorOff"

    wc = WNDCLASS()

    wc.style = 0

    # Cast callback to void pointer
    wc.lpfnWndProc = ctypes.cast(
        wnd_proc,
        ctypes.c_void_p
    )

    wc.cbClsExtra = 0

    wc.cbWndExtra = 0

    wc.hInstance = hInstance

    wc.hIcon = None

    wc.hCursor = None

    wc.hbrBackground = None

    wc.lpszMenuName = None

    wc.lpszClassName = class_name

    if not user32.RegisterClassW(
        ctypes.byref(wc)
    ):

        error = ctypes.get_last_error()

        # 1410 = class already exists
        if error != 1410:

            print(
                f"RegisterClassW failed: {error}"
            )

            sys.exit(1)

    hwnd = user32.CreateWindowExW(

        0,

        class_name,

        "Monitor Off",

        0,

        0,
        0,
        0,
        0,

        None,
        None,

        hInstance,

        None
    )

    if not hwnd:

        error = ctypes.get_last_error()

        print(
            f"CreateWindowExW failed: {error}"
        )

        sys.exit(1)

    if not add_tray_icon(hwnd):

        user32.DestroyWindow(
            hwnd
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Windows message loop
    # --------------------------------------------------------

    msg = wintypes.MSG()

    while user32.GetMessageW(
        ctypes.byref(msg),
        None,
        0,
        0
    ) > 0:

        user32.TranslateMessage(
            ctypes.byref(msg)
        )

        user32.DispatchMessageW(
            ctypes.byref(msg)
        )


# ------------------------------------------------------------
# Start
# ------------------------------------------------------------

if __name__ == "__main__":
    main()
