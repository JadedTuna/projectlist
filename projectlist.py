#!/usr/bin/env python
#coding: utf-8
import wx
import os
import sys
import sqlite3 as sql
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, TextEditMixin

projects = [
    [
        "linkchecker",
        "failed",
        "no",
        "/home/victor/Documents/Projects/linkchecker",
    ]
]
CREATE_CMD = ("CREATE TABLE Projects(Name TEXT,"
              "Status TEXT, GitHub TEXT, Path TEXT, Info TEXT)")

class CheckListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin, TextEditMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent,
                             style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        ListCtrlAutoWidthMixin.__init__(self)
        TextEditMixin.__init__(self)
        
        menu = wx.Menu()
        ID_ADD    = wx.NewId()
        ID_INFO   = wx.NewId()
        ID_REMOVE = wx.NewId()
        
        menu.Append(ID_ADD, "Add")
        menu.Append(ID_INFO, "Info")
        menu.Append(ID_REMOVE, "Remove")
        
        parent.Bind(wx.EVT_MENU, parent.onAdd, id=ID_ADD)
        parent.Bind(wx.EVT_MENU, parent.onInfo, id=ID_INFO)
        parent.Bind(wx.EVT_MENU, parent.onRemove, id=ID_REMOVE)
        self.popupmenu = menu
        
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.onBeginEdit)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onPopupMenu)
    
    def onPopupMenu(self, event):
        self.GetParent().PopupMenu(self.popupmenu)
    
    def onBeginEdit(self, event=None):
        if event.m_col == 0:
            return event.Veto()
        event.Skip()

class InfoDialog(wx.Frame):
    def __init__(self, parent, title, info):
        wx.Frame.__init__(self, parent, title="%s|info" % title.GetText())
        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.text.SetValue(info)

class Window(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Project list")
        
        ID_ADD    = wx.NewId()
        ID_INFO   = wx.NewId()
        ID_REMOVE = wx.NewId()
        ID_EXIT   = wx.NewId()
        ID_EXITNS = wx.NewId()
        
        menubar = wx.MenuBar()
        menu    = wx.Menu()
        menu.Append(ID_ADD, "Add")
        menu.Append(ID_INFO, "Info")
        menu.Append(ID_REMOVE, "Remove")
        menu.AppendSeparator()
        menu.Append(ID_EXIT, "Exit")
        menu.Append(ID_EXITNS, "Exit without saving")
        
        self.Bind(wx.EVT_MENU, self.onAdd, id=ID_ADD)
        self.Bind(wx.EVT_MENU, self.onInfo, id=ID_INFO)
        self.Bind(wx.EVT_MENU, self.onRemove, id=ID_REMOVE)
        self.Bind(wx.EVT_MENU, self.onCloseSave, id=ID_EXIT)
        self.Bind(wx.EVT_MENU, lambda evt: self.Destroy(), id=ID_EXITNS)
        
        menubar.Append(menu, "&Projects")
        self.SetMenuBar(menubar)
        
        self.listctrl = CheckListCtrl(self)
        self.listctrl.InsertColumn(0, "Name")
        self.listctrl.InsertColumn(1, "Status")
        self.listctrl.InsertColumn(2, "GitHub")
        self.listctrl.InsertColumn(3, "Path")
        self.Bind(wx.EVT_CLOSE, self.onCloseSave)
        self.load()
    
    def onAdd(self, event):
        dlg = wx.TextEntryDialog(self, "Enter project's name:", "New project")
        if dlg.ShowModal() == wx.ID_OK:
            text = dlg.GetValue()
            if text:
                for index in range(self.listctrl.GetItemCount()):
                    item = self.listctrl.GetItem(index, 0)
                    if item.GetText() == text:
                        wx.MessageBox(
                            "Project with entered name already exists",
                            "Error",
                            style=wx.ICON_ERROR|wx.OK)
                        return dlg.Destroy()
                row = [
                    text,
                    "idea",
                    "no",
                    "unknown"
                ]
                self.load_element(self.listctrl.GetItemCount(), row)
                self.infos.append("Info")
        dlg.Destroy()
    
    def onInfo(self, event):
        item = self.listctrl.GetFocusedItem()
        if item == -1: return
        title = self.listctrl.GetItem(item, 0)
        dialog = InfoDialog(self, title, self.infos[item])
        dialog.Show()
        self.infos[item] = dialog.text.GetValue()
    
    def onRemove(self, event):
        item = self.listctrl.GetFocusedItem()
        if item == -1: return
        dlg = wx.MessageDialog(self, "Are you sure?", "Remove project",
                               style=wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_OK:
            self.listctrl.DeleteItem(item)
            self.infos.pop(item)
        dlg.Destroy()
    
    def create(self, fn):
        con = sql.connect(fn)
        with con:
            cur = con.cursor()
            cur.execute(CREATE_CMD)
    
    def load(self, fn="projects.db"):
        self.fn = fn
        if not os.path.exists(fn):
            self.create(fn)
        self.listctrl.DeleteAllItems()
        con = sql.connect(fn)
        self.infos = []
        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM Projects")
            index = 0
            while True:
                row = cur.fetchone()
                if row is None: break
            
                self.load_element(index, row)
                self.infos.append(row[4])
                index += 1
    
    def load_element(self, index, item):
        self.listctrl.InsertStringItem(index, item[0])
        self.listctrl.SetStringItem(index, 1, item[1])
        self.listctrl.SetStringItem(index, 2, item[2])
        self.listctrl.SetStringItem(index, 3, item[3])
    
    def save_changes(self):
        con = sql.connect(self.fn)
        with con:
            cur = con.cursor()
            cur.execute("DROP TABLE IF EXISTS Projects")
            cur.execute(CREATE_CMD)
            for index in range(self.listctrl.GetItemCount()):
                data = [
                    self.listctrl.GetItem(index, 0).GetText(),
                    self.listctrl.GetItem(index, 1).GetText(),
                    self.listctrl.GetItem(index, 2).GetText(),
                    self.listctrl.GetItem(index, 3).GetText(),
                    self.infos[index]
                ]
                cur.execute("INSERT INTO Projects VALUES(?,?,?,?,?)", data)
    
    def onCloseSave(self, event):
        self.save_changes()
        self.Destroy()

app = wx.App()
window = Window()
window.Show()
app.MainLoop()
