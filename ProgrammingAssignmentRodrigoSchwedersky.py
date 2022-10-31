import logging
import os
import unittest
import vtk, qt, ctk, slicer
import SegmentStatistics
from slicer.ScriptedLoadableModule import *
from slicer.util import TESTING_DATA_URL
from slicer.util import VTKObservationMixin


# Rename "YourName" everywhere in this file to your first and last name. Also rename this file and its folder.
# You'll have to do the widget connections in ProgrammingAssignmentYourNameWidget.
# Do your work in the method ProgrammingAssignmentYourNameLogic.run.


class ProgrammingAssignmentRodrigoSchwedersky(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:

    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        applicant_name = "rodrigo_schwedersky"
        self.parent.title = "Programming Assignment: {}".format(applicant_name)
        self.parent.categories = ["Programming Assignment"]
        self.parent.dependencies = []
        self.parent.contributors = [applicant_name]
        self.parent.helpText = ""
        self.parent.acknowledgementText = ""


class ProgrammingAssignmentRodrigoSchwederskyWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """



  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Threshold"
    self.layout.addWidget(parametersCollapsibleButton)
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
    
    self.logic = ProgrammingAssignmentRodrigoSchwederskyLogic()
    
    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = True
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene(slicer.mrmlScene)
    self.inputSelector.setToolTip( "Pick the input." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # thresholdRangeSlider
    #
    self.thresholdRangeSlider1 = slicer.qMRMLVolumeThresholdWidget()
    parametersFormLayout.addRow(self.thresholdRangeSlider1)

    volNode = self.inputSelector.currentNode()
    self.thresholdRangeSlider1.setMRMLVolumeNode(volNode)
    
    
   
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # connections
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onInputVolumeSelectorChange)
    self.thresholdRangeSlider1.connect('thresholdValuesChanged(double, double)', self.onThresholdValuesChanged)


    self.initializeParameterNode()

    # Add vertical spacer
    self.layout.addStretch(1)
    
  def onInputVolumeSelectorChange(self):
    """ 
    """
    # Get the new volume node from the GUI selector
    newVolumeNode = self.inputSelector.currentNode()
    # Associate the threshold range slider with the new input node
    self.thresholdRangeSlider1.setMRMLVolumeNode(newVolumeNode)    
    # Since volume rendering multiple volumes doesn't work, first turn off
    # all rendering display nodes...
    self.logic.hideAllRenderedVolumes()
    if newVolumeNode is None:
      return
    # ... and then turn on volume rendering for the new volume
    volRenLogic = slicer.modules.volumerendering.logic()
    displayNode = volRenLogic.GetFirstVolumeRenderingDisplayNode(newVolumeNode)
    if not displayNode:
      displayNode = volRenLogic.CreateDefaultVolumeRenderingNodes(newVolumeNode)
    displayNode.SetFollowVolumeDisplayNode(1) # synchronize with Volumes module 
    displayNode.SetVisibility(1)
    # Update parameter node 
    self.updateParameterNodeFromGUI()


  def onThresholdValuesChanged(self, lower, upper):
    volNode = self._parameterNode.GetNodeReference('InputVolume')
    if volNode:
      self.logic.updateThresholdOnVolume(volNode, lower, upper)

  # def cleanup(self):
  #   pass
  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def enter(self):
    """
    Called each time the user opens this module.
    """
    # Make sure parameter node exists and observed
    self.initializeParameterNode()


  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore
    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()


  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.

    self.setParameterNode(self.logic.getParameterNode())

    # Select default input nodes if nothing is selected yet to save a few clicks for the user
    if not self._parameterNode.GetNodeReference("InputVolume"):
      firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
      if firstVolumeNode:
        self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())


  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """
    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()


  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # Update node selectors and sliders
    oldVolNode = self.inputSelector.currentNode()
    newVolNode = self._parameterNode.GetNodeReference("InputVolume")
    if newVolNode != oldVolNode:
      # Only update if there is a change (because this will trigger onInputVolumeSelectorChange function)
      self.inputSelector.setCurrentNode(newVolNode)
    self.thresholdRangeSlider1.setMRMLVolumeNode(self._parameterNode.GetNodeReference("InputVolume"))
    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    self._parameterNode.SetNodeReferenceID("InputVolume", self.inputSelector.currentNodeID)

    self._parameterNode.EndModify(wasModified)

#
# ScriptedLoadableModuleTemplateLogic
#

class ProgrammingAssignmentRodrigoSchwederskyLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def updateThresholdOnVolume(self, volNode, lower, upper):
    displayNode = volNode.GetDisplayNode()
    displayNode.SetThreshold(lower, upper)
    displayNode.ApplyThresholdOn()

  def hideAllRenderedVolumes(self):
    """Since volume rendering multiple volumes doesn't work, this function
    allows turning off of all volume renderings
    """
    dnListVtkGPU = slicer.mrmlScene.GetNodesByClass('vtkMRMLGPURayCastVolumeRenderingDisplayNode')
    dnListVtkGPU.UnRegister(slicer.mrmlScene)
    dnListVTKCPU = slicer.mrmlScene.GetNodesByClass('vtkMRMLCPURayCastVolumeRenderingDisplayNode')
    dnListVTKCPU.UnRegister(slicer.mrmlScene)
    # Convert to iterable python list
    vrDisplayNodesGPU = [dnListVtkGPU.GetItemAsObject(idx) for idx in range(dnListVtkGPU.GetNumberOfItems())]
    vrDisplayNodesCPU = [dnListVTKCPU.GetItemAsObject(idx) for idx in range(dnListVTKCPU.GetNumberOfItems())]
    vrDisplayNodesAll = vrDisplayNodesGPU + vrDisplayNodesCPU # concatenate lists
    # Loop over all display nodes
    for vrDisplayNode in vrDisplayNodesAll:
      vrDisplayNode.SetVisibility(0) # hide 

class ProgrammingAssignmentRodrigoSchwederskyTest(ScriptedLoadableModuleTest):
    """This is the test case for your scripted module.

    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_Skeleton1()

    def test_Skeleton1(self):
        pass
