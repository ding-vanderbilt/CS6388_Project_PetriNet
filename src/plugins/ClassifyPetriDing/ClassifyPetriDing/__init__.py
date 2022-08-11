"""
The following comments are based on the original file from Tamas Kecskes's StateMachineJoint example on GitHub 
The github repo is at https://github.com/kecso/StateMachineJoint
I modify the comments there to my own Plugin

This is where the implementation of the plugin code goes.
The ClassifyPetriDing-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('ClassifyPetriDing')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class ClassifyPetriDing(PluginBase):
    def main(self):
        # self.send_notification('This is just a test message!')
        name = self.core.get_attribute(self.active_node, 'name')
        self.send_notification('Interprete {0}'.format(name))
        self.places = None
        self.transitions = None
        self.is_free_choice = False
        self.is_state_machine = True
        self.is_marked_graph = True
        self.is_workflow_net = False
        self.collect_data()
        self.check_free_choice()
        self.check_state_machine()
        self.check_marked_graph()
        self.check_workflow_net()
        if self.is_free_choice:
            self.send_notification('It is a Free Choice Petri Net')
        else:
            self.send_notification('It is NOT a Free Choice Petri Net')

        if self.is_state_machine:
            self.send_notification('It is a State Machine Petri Net')
        else:
            self.send_notification('It is NOT a State Machine Petri Net')

        if self.is_marked_graph:
            self.send_notification('It is a Marked Graph Petri Net')
        else:
            self.send_notification('It is NOT a Marked Graph Petri Net')  

        if self.is_workflow_net:
            self.send_notification('It is a Workflow Net Petri Net')
        else:
            self.send_notification('It is NOT a Workflow Net Petri Net')
            
    def collect_data(self):
        """
        This function will go through all the node in the current active node.
        For each places, it is going to check the 

        """
        self.send_notification('Start Collect Data')
        self.places = {}
        self.transitions = {}
        nodes = self.core.load_own_sub_tree(self.active_node)

        for node in nodes:
            if self.core.is_instance_of(node, self.META['Place']):
                place_id = self.core.get_path(node)
                self.places[place_id] = {}
                # the src transtion so it is connected by Arc_TP
                self.places[place_id]['src'] = []
                # the dst transtion so it is connected by Arc_PT
                self.places[place_id]['dst'] = []
            if self.core.is_instance_of(node, self.META['Transition']):
                transition_id = self.core.get_path(node)
                self.transitions[transition_id] = {}
                # the src place so it is connected by Arc_PT
                self.transitions[transition_id]['src'] = []
                # the dst place so it is connected by Arc_TP
                self.transitions[transition_id]['dst'] = []

        for node in nodes:
            # Arc_PT means it is an Arc from Place to Transition
            # the src is Place
            # the dst is Transtion
            if self.core.is_instance_of(node, self.META['Arc_PT']):
                place_id = self.core.get_pointer_path(node, 'src')
                transition_id = self.core.get_pointer_path(node, 'dst')
                # Arc_PT goes from Place to Transtion
                self.places[place_id]['dst'].append(transition_id)
                self.transitions[transition_id]['src'].append(place_id)

            # Arc_TP means it is an Arc from Place to Transition
            # the src is Transition
            # the dst is Place
            if self.core.is_instance_of(node, self.META['Arc_TP']):
                place_id = self.core.get_pointer_path(node, 'dst')
                transition_id = self.core.get_pointer_path(node, 'src')
                # Arc_TP goes from Transtion to Place
                self.places[place_id]['src'].append(transition_id)
                self.transitions[transition_id]['dst'].append(place_id) 
    
    def check_free_choice(self):
        """
        Free-choice petri net
         - if the intersection of the inplaces sets of two transitions are not empty,
          then the two transitions should be the same
           (or in short, each transition has its own unique set if inplaces)

        Every arc is either the only arc going from the the place
         or only arc going to the transition

         if there is an arc from a place s to a transition t,
          then there must be an arc from any input place of t to any output transition of s.
        """
        self.send_notification('Test Free Choice')
        inplaces = set()
        for transition_id in self.transitions:
            transition = self.transitions[transition_id]
            inplaces.add(frozenset(transition['src']))
        if len(inplaces) + 1 == len(self.transitions):
            self.is_free_choice = True
        # p1 = len(set([frozenset(transition['src']) for transition in self.transitions.values()]))
        # p2 =  len(self.transitions)
        # self.send_notification(str(p1))
        # self.send_notification(str(p2))

        # if len(set([frozenset(transition['src']) for transition in self.transitions.values()])) + 1 == len(self.transitions):
        #     self.is_free_choice = True

    def check_state_machine(self):
        """
        State machine - a petri net is a state machine 
        if every transition has exactly one inplace and one outplace
        """
        self.send_notification('Test State Machine')
        for transition_id in self.transitions:
            src_place = self.transitions[transition_id]['src']
            dst_place = self.transitions[transition_id]['dst']
            if len(src_place) != 1 or len(dst_place) != 1:
                self.is_state_machine = False
                break

    def check_marked_graph(self):
        """
        Marked graph -
         a petri net is a marked graph if 
         every place has exactly one out transition 
         and one in transition.
        """
        self.send_notification('Test Marked Graph')
        for place_id in self.places:
            src_transition = self.places[place_id]['src']
            dst_transition = self.places[place_id]['dst']
            if len(src_transition) != 1 or len(dst_transition) != 1:
                self.is_marked_graph = False
                break

    def check_workflow_net(self):
        """
        Workflow net:
         a petri net is a workflow net if it has exactly one source place and one sink place 
        """
        self.send_notification('Test WorkFlow Net')
        source = False
        sink = False
        for place_id in self.places:
            src_transition = self.places[place_id]['src']
            dst_transition = self.places[place_id]['dst']
            if len(src_transition) == 0:
                source = not source
            if len(dst_transition) == 0:
                sink = not sink
        if source and sink:
            self.is_workflow_net = True








