import pickle
import os

class any_available: pass

class stater:

    def __getattribute__(self, name):
        attrs = pickle.load(open('state.info', 'rb')) if os.path.exists('state.info') else {}        
        if name == 'set_default':    
            return lambda **kwargs: pickle.dump({**kwargs, **attrs}, open('state.info', 'wb')) 
        else:
            return attrs[name] if name in attrs else None

    def __setattr__(self, name, value):
        attrs = pickle.load(open('state.info', 'rb')) if os.path.exists('state.info') else {}
        pickle.dump({**attrs, name: value}, open('state.info', 'wb'))   

state = stater()

import json
import uuid
import discord
import asyncio
from inspect import signature, Parameter, iscoroutine
from random import randint

client = discord.Client()
print('Initializing...')

# _ = uuid.uuid1()
# class webhook(object):
#     def __init__(self, schema):
#         self.schema = schema
#         self.aggregate = type('', (), {})()

#     @consider_state
#     def __call__(self, fun):
#         def parse_schema(json_str):
#             if self.adhers_to_schema(json.loads(json_str), self.schema):
#                 fun(self.aggregate)
#         return parse_schema

#     def adhers_to_schema(self, obj, schema_element):
#         if schema_element != _:

#             if isinstance(schema_element, list):
#                 for a, b in zip(obj, schema_element):
#                     if not self.adhers_to_schema(a, b):
#                         return False

#             elif isinstance(schema_element, dict):
#                 for k, v in schema_element.items():
#                     if not k in obj or not self.adhers_to_schema(obj[k], v):
#                         return False
#                     else:
#                         self.aggregate.__dict__[k] = obj[k]

#             else:
#                 if obj != schema_element:
#                     return False

#         return True
        

# @webhook(schema = {"obj": {"inner": _}})
# def parse(json, state):
#     print(json.inner, state)

# #parse('{"obj": {"inner": 3}}')

def make_discord_interface_decorator(deco):
    def inner(f = None, **kwargs):
        if f != None and (kwargs != {} or not hasattr(f, '__call__') or not hasattr(f, '__name__') or f.__name__ == '<lambda>' or f.__name__ in globals()):
            raise TypeError("An interface decorator can only receive keyword arguments")
        return deco(f) if f else lambda lf: deco(lf, **kwargs)
    return inner

async def resolve(obj):
    if iscoroutine(obj):
        await obj
    elif isinstance(obj, list) and all(iscoroutine(e) for e in obj):
        [await e for e in obj]
    else:
        pass

######################################################
available_commands = dict()
@make_discord_interface_decorator
def command(*args, prefix = '!', user = any_available, users = any_available, server = any_available, servers = any_available, channel = any_available, channels = any_available):
    fun, *_ = args

    def construct_list(singular, plurar):
        result_list = plurar
        if singular != any_available: 
            result_list = [singular] if plurar == any_available else [singular, *plurar]
        return result_list

    fun_details = {
        'users': construct_list(user, users), 
        'servers': construct_list(server, servers), 
        'channels': construct_list(channel, channels)
    }
        
    available_commands[f'{prefix}{fun.__name__}'] = (fun, fun_details)
    print(f"Added command {prefix}{fun.__name__}")

@client.event
async def on_message(msg):
    if msg.author.bot: return

    cmd_name, *args = msg.content.split(' ')
    if cmd_name not in available_commands: return
    cmd, cmd_details = available_commands[cmd_name]

    allowed_users, allowed_servers, allowed_channels = cmd_details['users'], cmd_details['servers'], cmd_details['channels']
    fails_check = lambda value, matches: matches != any_available and not value in matches
    if fails_check(f'{msg.author.name}#{msg.author.discriminator}', allowed_users): return
    if msg.guild and fails_check(msg.guild.name, allowed_servers): return
    if (str(msg.channel.type) == 'private' and allowed_channels != any_available) or (str(msg.channel.type) != 'private' and fails_check(msg.channel.name, allowed_channels)): return

    fun_params = signature(cmd).parameters
    fun_param_names = [param_name for param_name in fun_params.keys() if  param_name != 'message']

    reply = ""
    if len(fun_param_names) != len(args):
        reply = f"Error, expected {len(fun_param_names)} arguments (got {len(args)})\nExpected arguments: "
        reply += ', '.join([f'{arg_name}' + (f' (default: {fun_params.get(arg_name).default})' if fun_params.get(arg_name).default != Parameter.empty else '') for arg_name in fun_param_names])
    else:
        kwargs = {'message': msg} if 'message' in fun_params else {}
        reply = cmd(*args, **kwargs)

    await msg.channel.send(reply)
######################################################

@make_discord_interface_decorator
def loop(*args, seconds = 0, minutes = 0, hours = 0, between = None):
    fun, *_ = args
    async def loop_task():
        await client.wait_until_ready()
        while not client.is_closed():
            await resolve(fun())
            sleep_time = randint(between[0], between[1]) if between else (seconds + minutes * 60 + hours * 60 * 60)
            await asyncio.sleep(sleep_time)
    client.loop.create_task(loop_task())
    print(f"Added task {fun.__name__}")

def run(token = open('bot_token').read().strip()):
    client.run(token)