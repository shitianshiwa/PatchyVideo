
import time

from flask import render_template, request, jsonify, redirect, session

from init import app
from utils.interceptors import loginOptional, jsonRequest, loginRequiredJSON
from services.playlist import *
from utils.html import buildPageSelector

@app.route('/list/getcommontags.do', methods = ['POST'])
@loginOptional
@jsonRequest
def ajax_playlist_getcommontags_do(rd, data, user):
    tags = listCommonTags(data.pid)
    return "json", makeResponseSuccess(tags)

@app.route('/list/setcommontags.do', methods = ['POST'])
@loginRequiredJSON
@jsonRequest
def ajax_playlist_setcommontags_do(rd, user, data):
    updateCommonTags(data.pid, data.tags, user)

@app.route('/list/setcover.do', methods = ['POST'])
@loginRequiredJSON
@jsonRequest
def ajax_playlist_setcover_do(rd, user, data):
    new_list = updatePlaylistCoverVID(data.pid, data.vid, int(data.page), int(data.page_size), user)
    return "json", makeResponseSuccess(new_list)

@app.route('/list/delete.do', methods = ['POST'])
@loginRequiredJSON
@jsonRequest
def ajax_playlist_deletevideo_do(rd, user, data):
    new_list = removeVideoFromPlaylist(data.pid, data.vid, int(data.page), int(data.page_size), user)
    return "json", makeResponseSuccess(new_list)

@app.route('/list/moveup.do', methods = ['POST'])
@loginRequiredJSON
@jsonRequest
def ajax_playlist_moveup_do(rd, user, data):
    new_list = editPlaylist_MoveUp(data.pid, data.vid, int(data.page), int(data.page_size), user)
    return "json", makeResponseSuccess(new_list)

@app.route('/list/movedown.do', methods = ['POST'])
@loginRequiredJSON
@jsonRequest
def ajax_playlist_movedown_do(rd, user, data):
    new_list = editPlaylist_MoveDown(data.pid, data.vid, int(data.page), int(data.page_size), user)
    return "json", makeResponseSuccess(new_list)

@app.route('/lists/new.do', methods = ['POST'])
@loginRequiredJSON
@jsonRequest
def ajax_lists_new_do(rd, user, data):
    if data.pid :
        updatePlaylistInfo(data.pid, "english", data.title, data.desc, data.cover, user)
    else :
        pid = createPlaylist("english", data.title, data.desc, data.cover, user)
        return "json", makeResponseSuccess({"pid": pid})

